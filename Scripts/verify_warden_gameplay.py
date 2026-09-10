#!/usr/bin/env python3
"""Compare combat rules with the playable baseline while allowing visual work.

Run from any directory. This source regression check does not prove a model was
loaded or that a fight is playable; use -CombatQA and inspect actual game frames
as well. The default is the pre-integration HEAD, pinned so a later commit cannot
silently make an altered rule its own baseline. Pass --baseline REF to override.

Only comments and whitespace are ignored. Visual constructor work, BeginPlay,
UpdatePose, added members, WriteCombatSnapshot and RunCombatQA are deliberately
outside the protected function set. Player Tick is protected because it owns
action duration, stamina regeneration and dodge displacement.
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
BASELINE = "65a681b7a9c8e0bdfc862a90c70bffd3815c1410"
WARDEN = "Source/AshWell/AshWellWarden.cpp"
PLAYER = "Source/AshWell/AshWellCombatCharacter.cpp"
TOKEN = re.compile(
    r'//[^\n]*|/\*[\s\S]*?\*/|"(?:\\[\s\S]|[^"\\])*"'
    r"|'(?:\\[\s\S]|[^'\\])*'|[A-Za-z_][A-Za-z_0-9]*"
    r"|(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?[fFuUlL]*"
    r"|::|->|\+\+|--|&&|\|\||<=|>=|==|!=|\+=|-=|\*=|/=|<<|>>|[^\s]"
)
PROTECTED = {
    WARDEN: (
        "AAshWellWarden",
        (
            "Tick", "ChangeState", "TryStrike", "StepTowardTarget",
            "ReceiveMeleeHit", "GetAimPoint", "FaceTarget", "SetArenaBounds",
            "ActivateEncounter", "GetAttackProgress",
        ),
    ),
    PLAYER: (
        "AAshWellCombatCharacter",
        (
            "Attack", "Dodge", "ToggleLock", "UpdateAttack", "TakeDamage",
            "UpdateCamera", "IsInvulnerable", "SetAction", "Tick",
            "SetupPlayerInputComponent", "InputDirection", "MoveForwardCombat",
            "MoveRightCombat", "LookYawCombat", "LookPitchCombat", "SlowDown",
            "SlowUp", "Interact", "IsDead", "HasWon", "ShouldUpdateLocomotion",
        ),
    ),
}


def tokens(source: str) -> list[str]:
    return [part for part in TOKEN.findall(source)
            if not part.startswith("//") and not part.startswith("/*")]


def end_group(parts: list[str], start: int, opening: str, closing: str) -> int:
    depth = 0
    for index in range(start, len(parts)):
        if parts[index] == opening:
            depth += 1
        elif parts[index] == closing:
            depth -= 1
            if depth == 0:
                return index
    raise ValueError(f"Unbalanced {opening}{closing} in source")


def body(parts: list[str], class_name: str, name: str) -> list[str]:
    prefix = [class_name, "::", name, "("]
    matches = []
    for index in range(len(parts) - len(prefix) + 1):
        if parts[index:index + len(prefix)] != prefix:
            continue
        after_args = end_group(parts, index + 3, "(", ")") + 1
        while after_args < len(parts) and parts[after_args] in ("const", "noexcept"):
            after_args += 1
        if after_args < len(parts) and parts[after_args] == "{":
            end = end_group(parts, after_args, "{", "}")
            matches.append(parts[after_args + 1:end])
    if len(matches) != 1:
        raise ValueError(f"Expected one definition of {class_name}::{name}, found {len(matches)}")
    return matches[0]


def constants(parts: list[str]) -> dict[str, list[str]]:
    found = {}
    for index in range(len(parts) - 2):
        if parts[index:index + 2] != ["static", "constexpr"]:
            continue
        end = parts.index(";", index)
        assignment = parts.index("=", index, end)
        found[parts[assignment - 1]] = parts[index:end + 1]
    return found


def capsule_setup(parts: list[str]) -> list[str]:
    """Protect collider creation/root/config, not its visual children."""
    constructor = body(parts, "AAshWellWarden", "AAshWellWarden")
    statements = []
    start = 0
    for index, token in enumerate(constructor):
        if token != ";":
            continue
        statement = constructor[start:index + 1]
        start = index + 1
        if statement and (statement[0] == "Capsule"
                          or statement[:4] == ["SetRootComponent", "(", "Capsule", ")"]):
            statements.extend(statement)
    if not statements:
        raise ValueError("Could not extract Warden capsule setup")
    return statements


def git(*arguments: str) -> str:
    result = subprocess.run(["git", "-C", str(ROOT), *arguments], check=True,
                            capture_output=True, text=True)
    return result.stdout


def fingerprint(parts: list[str]) -> str:
    return hashlib.sha256("\n".join(parts).encode()).hexdigest()


def check(name: str, before: list[str], after: list[str]) -> dict:
    same = before == after
    result = {"check": name, "passed": same,
              "baseline_sha256": fingerprint(before), "current_sha256": fingerprint(after)}
    if not same:
        result["token_diff"] = list(difflib.unified_diff(
            before, after, fromfile="baseline", tofile="current", n=3, lineterm=""
        ))[:120]
    return result


def verify(reference: str) -> dict:
    commit = git("rev-parse", "--verify", f"{reference}^{{commit}}").strip()
    paths = [*PROTECTED, "Source/AshWell/AshWellWarden.h"]
    baseline = {path: tokens(git("show", f"{commit}:{path}")) for path in paths}
    current = {path: tokens((ROOT / path).read_text()) for path in paths}
    checks = []
    for path, (class_name, functions) in PROTECTED.items():
        for name in functions:
            checks.append(check(f"{class_name}::{name}",
                                body(baseline[path], class_name, name),
                                body(current[path], class_name, name)))
    header = "Source/AshWell/AshWellWarden.h"
    original_constants, new_constants = constants(baseline[header]), constants(current[header])
    if not original_constants:
        raise ValueError("No baseline Warden constants found")
    for name, declaration in original_constants.items():
        checks.append(check(f"Warden constant {name}", declaration, new_constants.get(name, [])))
    checks.append(check("Warden capsule creation/root/collision", capsule_setup(baseline[WARDEN]),
                        capsule_setup(current[WARDEN])))
    failures = [item["check"] for item in checks if not item["passed"]]
    return {
        "passed": not failures, "baseline": commit, "project": str(ROOT),
        "check_count": len(checks), "failures": failures, "checks": checks,
        "scope": "Source invariants only; visual assets and actual runtime require separate verification.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", default=BASELINE, help="Git ref; default is pre-integration HEAD")
    parser.add_argument("--output", type=Path, help="Also save the JSON report at this explicit path")
    arguments = parser.parse_args()
    try:
        result = verify(arguments.baseline)
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        result = {"passed": False, "error": str(error), "baseline": arguments.baseline}
    report = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if arguments.output:
        arguments.output.parent.mkdir(parents=True, exist_ok=True)
        arguments.output.write_text(report)
    print(report, end="")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
