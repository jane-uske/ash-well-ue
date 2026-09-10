#!/usr/bin/env python3
"""Audit real mounted-debug JSONL evidence; missing operations are UNVERIFIED.

Example:
  python3 Scripts/verify_mounted_debug_log.py Saved/MountedBoss/Debug/session.jsonl \
      --output Saved/MountedBoss/debug-verification.json

Exit codes: 0 all required observations passed; 1 contradictory/malformed evidence;
2 required observations missing. This does not launch UE or claim deterministic replay.
"""
from __future__ import annotations

import argparse
import collections
import json
import math
from pathlib import Path
from typing import Any


def number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def close(a: Any, b: Any, tolerance: float = 1e-4) -> bool:
    return number(a) and number(b) and abs(a - b) <= tolerance


def audit(path: Path, clock_tolerance: float, minimum_pause: float) -> dict[str, Any]:
    checks: dict[str, dict[str, Any]] = {}
    rows: list[dict[str, Any]] = []

    def check(name: str, status: str, reason: str, **evidence: Any) -> None:
        checks[name] = {"status": status, "reason": reason, **evidence}

    def lines(records: list[dict[str, Any]]) -> list[int]:
        return [record["_line"] for record in records]

    try:
        source = path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError) as error:
        return {"file": str(path.resolve()), "status": "failed", "checks": {
            "readable": {"status": "failed", "reason": str(error)}}}
    malformed = []
    raw_lines = source.splitlines()
    partial_tail = False
    for index, line in enumerate(raw_lines, 1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
            if not isinstance(record, dict):
                raise ValueError("JSON line is not an object")
            record["_line"] = index
            rows.append(record)
        except (ValueError, json.JSONDecodeError) as error:
            if index == len(raw_lines) and not source.endswith("\n"):
                partial_tail = True
            else:
                malformed.append({"line": index, "error": str(error)})
    check("jsonl", "failed" if malformed else "unverified" if partial_tail else "passed",
          "Malformed records" if malformed else "Last record is incomplete; writer may still be running" if partial_tail else "Every complete line is a JSON object",
          records=len(rows), errors=malformed)
    if not rows:
        check("events", "unverified", "No completed event records")
        return finish(path, checks, rows)

    by_event: dict[str, list[dict[str, Any]]] = collections.defaultdict(list)
    for row in rows:
        by_event[str(row.get("event", ""))].append(row)
    required = ("schema", "session", "event", "real_seconds", "world_seconds", "paused", "dilation", "player_action", "player_action_seconds", "player_iframe", "health", "stamina")
    missing = [{"line": row["_line"], "fields": [key for key in required if key not in row]} for row in rows]
    missing = [entry for entry in missing if entry["fields"]]
    sessions = sorted({str(row.get("session")) for row in rows})
    decreasing = []
    for previous, current in zip(rows, rows[1:]):
        if all(number(row.get("real_seconds")) for row in (previous, current)) and current["real_seconds"] < previous["real_seconds"]:
            decreasing.append([previous["_line"], current["_line"]])
    invalid_schema = [row["_line"] for row in rows if row.get("schema") != "ashwell.mounted.debug.v1"]
    check("event_integrity", "failed" if missing or decreasing or invalid_schema or len(sessions) != 1 else "passed",
          "Required event fields, one session and monotonic real time",
          missing=missing[:20], backwards_time=decreasing, invalid_schema=invalid_schema, sessions=sessions)

    starts, ends = by_event["session_start"], by_event["session_end"]
    environment_keys = ("engine", "platform", "cpu", "project", "map", "replay_scope", "viewport_width", "viewport_height", "trace_period_real_seconds", "character_ticks_when_paused")
    environment_missing = []
    if starts:
        environment_missing = [key for key in environment_keys if key not in starts[0] or starts[0][key] == ""]
    viewport_valid = bool(starts) and all(number(starts[0].get(key)) and starts[0][key] > 0 for key in ("viewport_width", "viewport_height"))
    check("session_environment", "passed" if starts and not environment_missing and viewport_valid else "unverified",
          "Environment and non-deterministic replay scope recorded" if starts and not environment_missing and viewport_valid else "Session environment or usable viewport evidence missing",
          lines=lines(starts), missing=environment_missing, environment={key: starts[0].get(key) for key in environment_keys} if starts else {})
    check("session_closed", "passed" if len(ends) == 1 and rows[-1].get("event") == "session_end" else "failed" if len(ends) > 1 else "unverified",
          "One terminal session_end observed" if len(ends) == 1 and rows[-1].get("event") == "session_end" else "A completed session_end has not been observed at the end of this file",
          lines=lines(ends))
    performance_keys = ("frame_count", "mean_frame_ms", "p50_frame_ms", "p95_frame_ms", "p99_frame_ms", "capture_enabled")
    perf = next((row for row in reversed(ends) if all(key in row for key in performance_keys)), None)
    if perf is None:
        check("performance", "unverified", "No completed performance summary", required=list(performance_keys))
    else:
        valid = all(number(perf[key]) and perf[key] > 0 for key in performance_keys[:-1]) and perf["p50_frame_ms"] <= perf["p95_frame_ms"] <= perf["p99_frame_ms"] and isinstance(perf["capture_enabled"], bool)
        check("performance", "passed" if valid else "failed", "Performance evidence exists; this is not a frame-rate acceptance threshold",
              line=perf["_line"], metrics={key: perf[key] for key in performance_keys})

    operations = [row for row in rows if row.get("event") in ("input", "attack_request", "heavy_request", "dodge_request")]
    contacts = by_event["contact_counts"]
    positive_contacts = [row for row in contacts if any(number(value) and value > 0 for value in (row.get("player_hits"), row.get("player_damage_count"), row.get("player_evaded_count"), row.get("boss", {}).get("contacts")))]
    check("input_and_operations", "passed" if operations else "unverified", "Recorded physical-key edges or player action requests" if operations else "No player input or operation request observed", lines=lines(operations)[:40])
    check("state_events", "passed" if by_event["boss_state"] and by_event["player_state"] else "unverified", "Boss and player state event streams required", boss_events=len(by_event["boss_state"]), player_events=len(by_event["player_state"]))
    check("contact_events", "passed" if positive_contacts else "unverified", "At least one actual contact/damage/evade count event required", lines=lines(positive_contacts))

    paused_rows = [row for row in rows if row.get("paused") is True]
    open_paused = [row["_line"] for row in paused_rows if row.get("boss_hit_window") is True or row.get("boss", {}).get("hit_window_open") is True]
    unknown_paused = [row["_line"] for row in paused_rows if "boss_hit_window" not in row]
    check("paused_hit_window", "failed" if open_paused else "unverified" if not paused_rows or unknown_paused else "passed",
          "Paused records must explicitly close the Boss damage window", paused_records=len(paused_rows), open_lines=open_paused, missing_lines=unknown_paused)
    intervals = []
    pending = None
    for index, row in enumerate(rows):
        if row.get("event") == "debug_pause" and row.get("detail") == "pause" and row.get("paused") is True:
            pending = (index, row)
        elif pending and row.get("event") in ("debug_reset_begin", "fixture_start", "debug_natural_ai", "session_end"):
            intervals.append({"status": "unverified", "pause_line": pending[1]["_line"], "reason": "Pause was interrupted by a reset, fixture, AI switch or session close"})
            pending = None
        elif pending and row.get("event") == "debug_pause" and row.get("paused") is False:
            start_index, start = pending
            interval = {"pause_line": start["_line"], "resume_line": row["_line"]}
            data = rows[start_index:index + 1]
            elapsed = row.get("real_seconds", 0) - start.get("real_seconds", 0)
            interval["real_pause_seconds"] = elapsed
            needed = all(number(item.get("world_seconds")) and number(item.get("boss", {}).get("state_time")) for item in data)
            if elapsed < minimum_pause or not needed:
                interval.update(status="unverified", reason="Pause too short or clock observations missing")
            else:
                world_drift = max(abs(item["world_seconds"] - start["world_seconds"]) for item in data)
                boss_drift = max(abs(item["boss"]["state_time"] - start["boss"]["state_time"]) for item in data)
                same_state = all(item.get("boss", {}).get("state") == start.get("boss", {}).get("state") and item.get("attack_serial") == start.get("attack_serial") for item in data)
                valid = world_drift <= clock_tolerance and boss_drift <= clock_tolerance and same_state
                interval.update(status="passed" if valid else "failed", world_clock_drift_seconds=world_drift, boss_clock_drift_seconds=boss_drift, state_and_serial_unchanged=same_state)
            intervals.append(interval)
            pending = None
    if pending:
        intervals.append({"status": "unverified", "pause_line": pending[1]["_line"], "reason": "No resume event yet"})
    pause_status = "failed" if any(item["status"] == "failed" for item in intervals) else "passed" if any(item["status"] == "passed" for item in intervals) else "unverified"
    check("pause_resume_clocks", pause_status, "A real pause/resume must preserve world clock, Boss state clock, state and attack serial", tolerance_seconds=clock_tolerance, minimum_real_pause_seconds=minimum_pause, intervals=intervals)

    speed_events = by_event["debug_speed"]
    slow_events = [row for row in speed_events if row.get("detail") == "0.25x"]
    restore_events = [row for row in speed_events if row.get("detail") == "1x"]
    wrong_speed = [row["_line"] for row in slow_events if not close(row.get("dilation"), .25)] + [row["_line"] for row in restore_events if not close(row.get("dilation"), 1)]
    speed_evidence = []
    for wanted, candidates in ((.25, slow_events), (1.0, restore_events)):
        found = False
        for control in candidates:
            later = []
            for row in rows:
                if row["_line"] <= control["_line"]:
                    continue
                if row.get("event") in ("debug_speed", "session_end"):
                    break
                if row.get("event") == "trace" and row.get("paused") is False and close(row.get("dilation"), wanted):
                    later.append(row)
            if later and number(control.get("world_seconds")) and later[-1]["world_seconds"] > control["world_seconds"]:
                found = True
                speed_evidence.append({"dilation": wanted, "control_line": control["_line"], "trace_lines": lines(later)})
                break
        if not found:
            speed_evidence.append({"dilation": wanted, "status": "unverified", "reason": "No matching live trace with advancing world time after this speed control"})
    speed_ok = len(speed_evidence) == 2 and all("control_line" in item for item in speed_evidence) and any(r["_line"] > s["_line"] for r in restore_events for s in slow_events)
    check("slow_and_restore", "failed" if wrong_speed else "passed" if speed_ok else "unverified", "Observe 0.25x, subsequent live simulation, and a later restoration to 1x", incorrect_value_lines=wrong_speed, evidence=speed_evidence)

    resets = by_event["debug_reset_complete"]
    reset_failures = []
    for row in resets:
        boss = row.get("boss", {})
        valid = close(row.get("health"), 100) and close(row.get("stamina"), 100) and row.get("player_action") == "idle" and boss.get("state") == "idle" and row.get("boss_hit_window") is False and close(boss.get("health"), boss.get("maximum_health"))
        if not valid:
            reset_failures.append(row["_line"])
    check("quick_reset", "failed" if reset_failures else "passed" if resets else "unverified", "Reset handler must restore player HP/stamina 100 and a full-health idle Boss with closed window; physical F4 routing also needs UI evidence", lines=lines(resets), invalid_lines=reset_failures)
    ai_events = by_event["debug_natural_ai"]
    ai_results = []
    for control in ai_events:
        if control.get("single_attack_mode") is not False or control.get("boss", {}).get("state") not in ("approach", "windup", "active", "recovery"):
            ai_results.append({"status": "failed", "line": control["_line"], "reason": "F5 did not restore a live natural-AI state"})
            continue
        subsequent = []
        for row in rows:
            if row["_line"] <= control["_line"]:
                continue
            if row.get("event") in ("debug_reset_begin", "fixture_start", "session_end"):
                break
            if row.get("single_attack_mode") is False and row.get("boss", {}).get("state") in ("windup", "active") and number(row.get("attack_serial")) and row["attack_serial"] > control.get("attack_serial", -1):
                subsequent.append(row)
        ai_results.append({"status": "passed" if subsequent else "unverified", "line": control["_line"], "new_natural_attack_lines": lines(subsequent), "reason": "Natural AI must autonomously select a subsequent attack"})
    ai_status = "failed" if any(item["status"] == "failed" for item in ai_results) else "passed" if any(item["status"] == "passed" for item in ai_results) else "unverified"
    check("natural_ai_restore", ai_status, "F5 handler state and subsequent autonomous attack required", evidence=ai_results)
    return finish(path, checks, rows)


def finish(path: Path, checks: dict[str, Any], rows: list[dict[str, Any]]) -> dict[str, Any]:
    statuses = collections.Counter(value["status"] for value in checks.values())
    status = "failed" if statuses["failed"] else "unverified" if statuses["unverified"] else "passed"
    return {"file": str(path.resolve()), "status": status, "records": len(rows), "counts": dict(statuses), "checks": checks,
            "limitations": ["This audits logged behavior, not physical key routing or visual quality.", "Missing actions and an open session remain unverified.", "Input/event traces are not a deterministic or bit-exact replay.", "Performance summary presence does not establish acceptable performance."]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("logs", type=Path, nargs="+", help="One or more real debug JSONL sessions")
    parser.add_argument("--output", type=Path, help="Write the same JSON report to this path")
    parser.add_argument("--clock-tolerance", type=float, default=1e-4, help="Allowed pause clock drift in seconds (default 0.0001)")
    parser.add_argument("--minimum-pause", type=float, default=.15, help="Minimum observed wall-clock pause in seconds (default 0.15)")
    args = parser.parse_args()
    if args.clock_tolerance < 0 or args.minimum_pause <= 0:
        parser.error("Clock tolerance must be nonnegative and minimum pause must be positive")
    reports = [audit(path, args.clock_tolerance, args.minimum_pause) for path in args.logs]
    status = "failed" if any(report["status"] == "failed" for report in reports) else "unverified" if any(report["status"] == "unverified" for report in reports) else "passed"
    result = {"schema": "ashwell.mounted.debug.verification.v1", "status": status, "reports": reports}
    serialized = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(serialized + "\n", encoding="utf-8")
    print(serialized)
    return 1 if status == "failed" else 2 if status == "unverified" else 0


if __name__ == "__main__":
    raise SystemExit(main())
