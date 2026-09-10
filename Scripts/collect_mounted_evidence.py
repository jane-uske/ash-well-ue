#!/usr/bin/env python3
"""Archive one completed mounted runtime run, without starting Unreal.

Case assignment uses session_start.utc in [case start, next case start).
Recorded actor Z is separate from the requested parabola apex. These are
automated fixture observations, never a claim of human play or visual approval.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import shutil
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ENGINE = Path("/Users/Shared/Epic Games/UE_5.8/Engine")
CASE_FILES = ("started.json", "result.json", "probe.json", "engine.log", "screenshot.png")
INTEGRATION_FILES = (
    "Source/AshWell/AshWellCombatCharacter.cpp",
    "Source/AshWell/AshWellCombatCharacter.h",
    "Source/AshWell/AshWellIntroCharacter.cpp",
    "Source/AshWell/AshWellIntroGameMode.cpp",
    "Source/AshWell/AshWellIntroHUD.cpp",
    "Source/AshWell/AshWellBattleFX.cpp",
    "Source/AshWell/AshWellBattleFX.h",
    "Source/AshWell/AshWell.Build.cs",
    "Source/AshWell/MountedGallopDistance.inl",
    "AshWell.uproject",
    "Config/DefaultEngine.ini",
    "Config/DefaultInput.ini",
    "Scripts/launch_mounted_boss.command",
    "Scripts/test_mounted_runtime.py",
    "Scripts/collect_mounted_evidence.py",
)


def utc(value: str) -> datetime:
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None:
        raise ValueError(f"UTC timestamp lacks timezone: {value}")
    return result.astimezone(timezone.utc)


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def digest(path: Path) -> str:
    sha = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            sha.update(chunk)
    return sha.hexdigest()


def relative(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def command(*args: str):
    try:
        result = subprocess.run(args, text=True, capture_output=True, timeout=10, check=True)
        return result.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return None


def read_session(path: Path):
    rows, errors = [], []
    with path.open(encoding="utf-8-sig") as stream:
        for line_number, line in enumerate(stream, 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
                rows.append((line_number, row))
            except json.JSONDecodeError as exc:
                errors.append({"line": line_number, "error": str(exc)})
    start = next((row for _, row in rows if row.get("event") == "session_start"), None)
    return {"path": path, "rows": rows, "start": start, "parse_errors": errors}


def analyze_session(session, archived_path: str):
    rows, start = session["rows"], session["start"]
    initial_z = start.get("boss", {}).get("z")
    leap_trace = [
        (line, row) for line, row in rows
        if row.get("event") == "trace"
        and row.get("boss", {}).get("attack") == "leap_shield"
        and row.get("boss", {}).get("state") == "active"
        and isinstance(row.get("boss", {}).get("z"), (int, float))
    ]
    peak = max(leap_trace, key=lambda item: item[1]["boss"]["z"]) if leap_trace else None
    height = peak[1]["boss"]["z"] - initial_z if peak and isinstance(initial_z, (int, float)) else None
    end_rows = [(line, row) for line, row in rows if row.get("event") == "session_end"]
    end = end_rows[-1][1] if end_rows else None
    perf_fields = ("frame_count", "mean_frame_ms", "p50_frame_ms", "p95_frame_ms", "p99_frame_ms", "capture_enabled")
    contacts = []
    previous_contacts = 0
    for line, row in rows:
        boss = row.get("boss", {})
        contact_count = boss.get("contacts", previous_contacts)
        if contact_count > previous_contacts:
            contacts.append({
                "line": line, "utc": row.get("utc"), "event": row.get("event"),
                "attack": boss.get("attack"), "active_time_s": boss.get("state_time"),
                "actual_actor_z_cm": boss.get("z"), "shield_bottom_proxy_gap_cm": boss.get("shield_ground_gap_cm"),
                "player_health_at_event": row.get("health"), "contact_count": contact_count,
                "health_timing_note": "damage_applied event is emitted before Health subtraction; use the next trace or final probe for resulting HP.",
            })
        previous_contacts = contact_count
    return {
        "log": archived_path,
        "session_id": start.get("session"), "session_start_utc": start.get("utc"),
        "session_end_present": end is not None, "parse_errors": session["parse_errors"],
        "engine": start.get("engine"), "cpu": start.get("cpu"), "platform": start.get("platform"),
        "viewport": [start.get("viewport_width"), start.get("viewport_height")],
        "actual_leap_height_observation": {
            "method": "trace event boss.z minus session_start boss.z; actual actor locations, not desired parabola",
            "ground_baseline_z_cm": initial_z,
            "trace_samples_during_active_leap": len(leap_trace),
            "sampled_max_actual_height_cm": height,
            "actual_height_observed": height > 20 if height is not None else None,
            "peak_line": peak[0] if peak else None,
            "peak_utc": peak[1].get("utc") if peak else None,
            "limits": "0.2 s trace sampling gives a sampled lower bound on peak, not exact apex or visual quality. maximum_leap_height_cm is deliberately excluded.",
        },
        "contact_observations": contacts,
        "frame_performance": {key: end[key] for key in perf_fields if end and key in end},
        "performance_limits": "Session frame interval statistics include fixture/logging/rendering overhead; not GPU timing, 1% low FPS or sustained full-fight benchmark.",
    }


def collect(run: Path, destination: Path, engine: Path, dry_run: bool):
    report_path = run / "test-results.json"
    report = read_json(report_path)
    if report.get("status") != "complete" or not report.get("finished_utc"):
        raise ValueError("Run is not complete; no evidence copied.")
    requested = report.get("requested_cases", [])
    results = report.get("results", [])
    if len(requested) != len(set(requested)) or set(requested) != {row["case"] for row in results}:
        raise ValueError("Requested cases and results do not match uniquely.")
    if any(Path(case).name != case for case in requested):
        raise ValueError("Case names must be plain directory names.")
    case_starts = [(case, utc(read_json(run / case / "started.json")["started_utc"])) for case in requested]
    if any(case_starts[i][1] >= case_starts[i + 1][1] for i in range(len(case_starts) - 1)):
        raise ValueError("Case start times are not strictly increasing.")
    finished = utc(report["finished_utc"])
    if case_starts and finished <= case_starts[-1][1]:
        raise ValueError("Run finished timestamp does not follow final case start.")
    sessions, unmatched_errors = [], []
    for path in sorted((ROOT / "Saved/MountedBoss/Debug").glob("*.jsonl")):
        session = read_session(path)
        if session["start"] and session["start"].get("utc"):
            sessions.append(session)
        else:
            unmatched_errors.append(relative(path))
    index = {row["case"]: row for row in results}
    cases, copies = [], [(report_path, destination / "test-results.json")]
    for i, (case, started) in enumerate(case_starts):
        end = case_starts[i + 1][1] if i + 1 < len(case_starts) else finished
        matched = [session for session in sessions if started <= utc(session["start"]["utc"]) < end]
        files, missing = {}, []
        for name in CASE_FILES:
            source = run / case / name
            if source.is_file():
                target = destination / case / name
                copies.append((source, target)); files[name] = relative(target)
            else:
                missing.append(name)
        details = []
        for session in matched:
            target = destination / case / "debug" / session["path"].name
            copies.append((session["path"], target))
            details.append(analyze_session(session, relative(target)))
        probe = read_json(run / case / "probe.json") if (run / case / "probe.json").is_file() else {}
        boss = probe.get("boss", {})
        cases.append({
            "case": case, "passed": index[case].get("passed", False),
            "failed_checks": index[case].get("failed_checks", []), "error": index[case].get("error"),
            "files": files, "missing_files": missing,
            "debug_matching_interval_utc": {"inclusive_start": started.isoformat(), "exclusive_end": end.isoformat()},
            "debug_sessions": details,
            "loop_or_fixture_outcome": {
                "player_hits": probe.get("hits"), "player_attacks": probe.get("attacks"),
                "player_dodges": probe.get("dodges"), "player_damage_count": probe.get("damage_count"),
                "boss_strikes": boss.get("strikes"), "player_dead": probe.get("dead"),
                "player_won": probe.get("won"), "player_health": probe.get("health"),
                "boss_health": boss.get("health"), "phase_observed": probe.get("phase_observed"),
                "terminal": "victory" if probe.get("won") else "death" if probe.get("dead") else "fixture_end",
                "provenance": "Automated fixture; loop uses forced charge opening followed by natural Boss decisions and scripted real player action interfaces.",
            },
        })
    build_log = ROOT / "Saved/MountedBoss/build.log"
    if build_log.is_file():
        copies.append((build_log, destination / "build.log"))
    version_file = engine / "Build/Build.version"
    if version_file.is_file():
        copies.append((version_file, destination / "UE-Build.version.json"))
    if dry_run:
        return {"dry_run": True, "run_id": report["run_id"], "run_passed": report.get("passed"),
                "cases": len(cases), "debug_sessions": sum(len(c["debug_sessions"]) for c in cases),
                "files_to_copy": len(copies), "bytes_to_copy": sum(p.stat().st_size for p, _ in copies),
                "destination": str(destination), "cases_missing_debug": [c["case"] for c in cases if not c["debug_sessions"]]}
    if destination.exists() and any(destination.iterdir()):
        raise ValueError("Destination is not empty; preserve the existing archive or choose --destination.")
    destination.mkdir(parents=True, exist_ok=True)
    copied = []
    for source, target in copies:
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        copied.append({"source": relative(source), "archived": relative(target), "bytes": target.stat().st_size, "sha256": digest(target)})
    paths = set(ROOT / name for name in INTEGRATION_FILES)
    paths.update((ROOT / "Source/AshWell").glob("AshWellMounted*.*"))
    sources = [{"path": relative(path), "sha256": digest(path),
                "mtime_utc": datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat(),
                "changed_after_run_started": path.stat().st_mtime > utc(report["started_utc"]).timestamp()}
               for path in sorted(paths) if path.is_file()]
    compiled_changed = [row["path"] for row in sources if row["path"].startswith("Source/") and row["changed_after_run_started"]]
    system = {
        "collected_utc": datetime.now(timezone.utc).isoformat(),
        "os": platform.system(), "os_release": platform.release(), "architecture": platform.machine(),
        "macos_product_version": command("/usr/bin/sw_vers", "-productVersion"),
        "macos_build_version": command("/usr/bin/sw_vers", "-buildVersion"),
        "cpu": command("/usr/sbin/sysctl", "-n", "machdep.cpu.brand_string"),
        "hardware_model": command("/usr/sbin/sysctl", "-n", "hw.model"),
        "memory_bytes": command("/usr/sbin/sysctl", "-n", "hw.memsize"),
        "engine_build_version": read_json(version_file) if version_file.is_file() else None,
        "runtime_engines": sorted({s["engine"] for c in cases for s in c["debug_sessions"] if s["engine"]}),
        "source_snapshot": sources,
        "compiled_sources_modified_after_run_started": compiled_changed,
        "source_snapshot_limit": "Hashes taken at evidence collection. Timestamps can detect later edits but do not prove which sources produced a binary; pair with build log and preserved binary hash.",
    }
    binary = ROOT / "Binaries/Mac/libUnrealEditor-AshWell.dylib"
    system["project_binary"] = {"path": relative(binary), "sha256": digest(binary), "bytes": binary.stat().st_size} if binary.is_file() else None
    write_json(destination / "system-and-source.json", system)
    summary = {
        "schema_version": 1, "run_id": report["run_id"], "source_run": relative(run),
        "started_utc": report["started_utc"], "finished_utc": report["finished_utc"],
        "automated_suite_passed": report.get("passed", False),
        "case_count": len(cases), "passed_case_count": sum(c["passed"] for c in cases),
        "visual_acceptance_passed": False, "human_playtest_certified": False,
        "cases": cases, "copied_files": copied,
        "unmatched_debug_files_without_session_start": unmatched_errors,
        "limits": [
            "Only one completed run is collected. Failed assertions remain failures.",
            "UTC interval matching assumes no unrelated mounted session ran during a case interval; session count and raw files are retained for inspection.",
            "Missing screenshots or session logs are recorded, not treated as success.",
            "Actual airborne evidence uses sampled actor z, never maximum_leap_height_cm desired trajectory.",
            "Camera projection, input fixture and fixed-Boss victory are narrower than visual, physical-key and human-combat acceptance.",
        ],
    }
    write_json(destination / "evidence-summary.json", summary)
    return {"archive": str(destination), "run_id": report["run_id"], "cases": len(cases),
            "passed": summary["passed_case_count"], "automated_suite_passed": summary["automated_suite_passed"],
            "compiled_sources_modified_after_run_started": compiled_changed}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path, help="Completed Saved/MountedBoss/runs/<run-id> directory")
    parser.add_argument("--destination", type=Path, default=ROOT / "Docs/Verification/MountedBoss/final-runtime")
    parser.add_argument("--engine", type=Path, default=DEFAULT_ENGINE, help="UE Engine directory")
    parser.add_argument("--dry-run", action="store_true", help="Validate and match sessions without copying")
    args = parser.parse_args()
    try:
        result = collect(args.run.resolve(), args.destination.resolve(), args.engine.resolve(), args.dry_run)
    except (OSError, ValueError, KeyError) as exc:
        print(f"Evidence collection failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
