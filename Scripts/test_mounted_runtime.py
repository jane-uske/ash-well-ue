#!/usr/bin/env python3
"""Run fresh, rendered UE mounted-combat fixtures; never terminate unrelated UE PIDs.

No arguments runs the 14 collision/action cases. Use --all for lifecycle, movement,
camera and input checks, or name individual cases. A pass is a runtime assertion,
not visual approval of horse gait, rider animation, lighting or camera occlusion.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import math
from pathlib import Path
import re
import subprocess
import sys
import time
import uuid


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "Saved/MountedBoss"
ATTACK_DAMAGE = {"sweep": 27, "overhead": 34, "charge": 32, "body_check": 19, "rear": 36, "leap_shield": 38}
DEFAULT_CASES = ["light", "heavy", "miss", "body"] + [
    f"{prefix}_{attack}" for prefix in ("hit", "dodge") for attack in ATTACK_DAMAGE
]
ALL_CASES = DEFAULT_CASES + ["movement", "camera", "disengage", "phase", "victory", "retry", "input", "natural_charge", "death", "cleanup", "loop"]


def finite(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def near(value: object, expected: float, tolerance: float = 0.05) -> bool:
    return finite(value) and abs(value - expected) <= tolerance


def check_fixture(case: str, data: dict, engine_log: str, expected_hp: float = 900) -> dict[str, bool]:
    """Missing fields fail the check that needs them; no truthy fallback for evidence."""
    boss = data.get("boss") if isinstance(data.get("boss"), dict) else {}
    checks = {
        "completed": data.get("complete") is True,
        "correct_probe": data.get("probe") == case,
        "correct_map": "MountedCourtyard" in str(data.get("map", "")),
        "hero_v02_loaded": data.get("hero_v02") is True,
        "horse_visual_loaded": boss.get("horse_visual") is True,
        "rider_visual_loaded": boss.get("rider_visual") is True,
        "finite_health": finite(data.get("health")) and 0 <= data["health"] <= 100,
        "finite_stamina": finite(data.get("stamina")) and -0.01 <= data["stamina"] <= 100.01,
        "stamina_never_negative": finite(data.get("min_stamina")) and data["min_stamina"] >= -0.01,
        "fixture_assertions_passed": data.get("failures") == 0,
        "no_global_slowdown": near(data.get("min_dilation"), 1, 0.005),
        "no_fatal_error": not re.search(r"Fatal error:|Assertion failed:|Unhandled Exception:|\*\*\* SIGSEGV", engine_log),
        "no_hero_load_error": not re.search(r"(?:LoadErrors|Failed to load|Couldn't find file).*(?:HeroComplete|MountedBoss)", engine_log),
        "hero_material_compiles": not re.search(r"M_Hero(?:Body|Cloth).*Failed to compile Material", engine_log),
        "cloth_scale_valid": "has a non uniform scale, and has a cloth simulation attached" not in engine_log,
    }
    if case in ("light", "heavy"):
        cost, damage = (12, 40) if case == "light" else (34, 55)
        checks.update(
            one_attack=data.get("attacks") == 1,
            one_hit=data.get("hits") == 1,
            correct_boss_damage=near(boss.get("health"), expected_hp - damage),
            attack_cost_observed=finite(data.get("min_stamina")) and data["min_stamina"] <= 100 - cost + 0.5,
            player_unharmed=near(data.get("health"), 100) and data.get("damage_count") == 0,
        )
    elif case == "shield_block":
        checks.update(one_attack=data.get('attacks')==1,one_visible_shield_contact=boss.get('shield_blocks')==1,
                      no_body_damage=near(boss.get('health'),expected_hp),no_body_hit=data.get('hits')==0,
                      full_attack_cost=finite(data.get('min_stamina')) and data['min_stamina']<=66.5,
                      shield_cue_started='AW_MOUNTED_AUDIO cue=SC_ShieldBlock' in engine_log)
    elif case == "miss":
        checks.update(
            attack_attempted=data.get("attacks", 0) >= 1,
            no_hit=data.get("hits") == 0,
            boss_unharmed=near(boss.get("health"), expected_hp),
            player_unharmed=near(data.get("health"), 100) and data.get("damage_count") == 0,
            miss_still_costs_stamina=finite(data.get("min_stamina")) and data["min_stamina"] <= 88.5,
        )
    elif case == "body":
        checks.update(
            no_passive_body_damage=near(data.get("health"), 100) and data.get("damage_count") == 0,
            boss_unharmed=near(boss.get("health"), expected_hp),
            body_did_not_overlap=near(data.get("body_penetration_seconds"),0,.001) and finite(data.get("body_min_gap_cm")) and data["body_min_gap_cm"]>=-.25,
            actually_approached_body=finite(data.get("body_min_gap_cm")) and data["body_min_gap_cm"] < 8,
            no_weapon_strike=boss.get("strikes") == 0,
        )
    elif case.startswith("hit_") or case.startswith("dodge_") or case=="natural_charge":
        dodge, attack = case.startswith("dodge_"), case.split("_", 1)[1]
        source = "area_contacts" if attack in ("rear","leap_shield") else "body_contacts" if attack == "body_check" else "weapon_contacts"
        checks.update(
            correct_attack=boss.get("attack") == attack,
            strike_executed=boss.get("strikes", 0) >= 1,
            heading_stayed_committed=finite(boss.get("committed_yaw_drift")) and boss["committed_yaw_drift"] < 0.2,
            readable_commit_lead=(finite(boss.get("commit_at_seconds")) and finite(boss.get("windup_seconds"))
                                  and 0 <= boss["commit_at_seconds"] < boss["windup_seconds"]),
            explicit_recovery=finite(boss.get("recovery_seconds")) and boss["recovery_seconds"] >= 0.65,
        )
        if attack=="leap_shield":checks.update(root_left_ground=boss.get("maximum_leap_height_cm",0)>140, landed=boss.get("leap_landed") is True)
        if dodge:
            checks.update(
                one_dodge=data.get("dodges") == 1,
                unharmed=near(data.get("health"), 100) and data.get("damage_count") == 0,
                # A spatial dodge is legitimate; the matching hit fixture is the control.
                # Do not label it a test of i-frames when no contact happened.
                resolved_attack=(finite(data.get("evaded")) and data["evaded"] >= 1) or boss.get("contacts") == 0,
                dodge_cost_observed=finite(data.get("min_stamina")) and data["min_stamina"] <= 72.5,
            )
        else:
            checks.update(
                correct_damage=near(data.get("health"), 100 - ATTACK_DAMAGE[attack]),
                damaged_once=data.get("damage_count") == 1,
                no_unrequested_dodge=data.get("dodges") == 0,
                correct_contact_source=boss.get(source) == 1,
                no_duplicate_contact=boss.get("contacts") == 1,
            )
        if case in ('hit_charge','dodge_charge') and boss.get('standard_sample') is True:
            events=re.findall(r'AW_MOUNTED_AUDIO cue=SC_HalberdSwing[^\n]*clock=([0-9.]+)',engine_log)
            expected=json.loads((ROOT/'SourceAssets/MountedReferenceProduction/charge-timing.json').read_text())['phase_seconds']['strike']
            checks.update(single_swing_cue=len(events)==1,swing_at_strike=bool(events) and abs(float(events[0])-expected)<.06)
            checks['contact_audio_once_or_absent']=engine_log.count('AW_MOUNTED_AUDIO cue=SC_WeaponHit ')==(0 if dodge else 1)
        if boss.get('standard_sample') is True and attack in ('rear','leap_shield'):
            checks['one_landing_sound']=engine_log.count('AW_MOUNTED_AUDIO cue=SC_Landing ')==1
            checks['one_body_sound_on_hit_only']=engine_log.count('AW_MOUNTED_AUDIO cue=SC_BodyHit ')==(0 if dodge else 1)
    elif case in ("cleanup","sample_cleanup"):
        checks.update(cancelled=boss.get("cancelled_attacks",0)>=1, no_late_damage=data.get("damage_count")==0, no_open_window=boss.get("hit_window_open") is False, duplicate_rejected=boss.get("duplicate_receive_rejected",0)>=1, grounded=near(boss.get("ground_clearance_cm"),0) and boss.get("ground_supported") is True, cleanup_steps=data.get("step",0)>=5)
        if case=='sample_cleanup':checks.update(notify_windows_exercised=boss.get('window_begins',0)>=2, montage_stopped=boss.get('montage_playing') is False, notify_cleared=boss.get('notify_window') is False)
    elif case=='sample_pre_cancel':
        checks.update(cancelled_before_window=data.get('step')==4 and boss.get('cancelled_attacks',0)>=1,no_late_notify=boss.get('window_begins')==0,window_closed=boss.get('notify_window') is False,montage_stopped=boss.get('montage_playing') is False,no_late_damage=data.get('damage_count')==0)
    elif case == "loop":
        checks.update(player_dodged=data.get("dodges",0)>=1, player_counter_hit=data.get("hits",0)>=1, boss_continued=boss.get("strikes",0)>=2, terminal_result=data.get("dead") is True or data.get("won") is True)
    elif case == "movement":
        checks.update(
            hoof_bones_valid=boss.get("hoof_bones_valid") is True,
            footfall_events=boss.get("hoof_contacts",0)>4,
            travelled=finite(boss.get("distance_travelled_cm")) and boss["distance_travelled_cm"] > 800,
            walk_clip_loaded=boss.get("walk_loaded") is True,
            run_clip_loaded=boss.get("run_loaded") is True,
            grounded=finite(boss.get("ground_clearance_cm")) and abs(boss["ground_clearance_cm"]) < 10 and boss.get("ground_supported") is True,
            stayed_in_arena=(finite(boss.get("x")) and finite(boss.get("y"))
                             and abs(boss["x"]) < 2400 and abs(boss["y"]) < 1900),
            remained_alive=data.get("dead") is False and boss.get("state") != "dead",
        )
    elif case == "camera":
        checks.update(
            at_least_five_positions=finite(data.get("step")) and data["step"] >= 5,
            no_environment_penetration=near(data.get("camera_overlap_seconds"), 0, 0.001),
            sampled=finite(data.get("camera_samples")) and data["camera_samples"] >= 30,
            target_in_frame=(finite(data.get("camera_visible")) and finite(data.get("camera_samples"))
                             and data["camera_samples"] > 0 and data["camera_visible"] / data["camera_samples"] >= 0.95),
        )
    elif case == "disengage":
        checks.update(
            returned_and_reset=boss.get("reset_count", 0) >= 1 and boss.get("state") == "idle",
            player_restored=near(data.get("health"), 100) and near(data.get("stamina"), 100),
            boss_restored=near(boss.get("health"), expected_hp),
            encounter_stopped=data.get("engaged") is False,
            lock_released=data.get("locked") is False,
            at_exit=finite(data.get("player_x")) and data["player_x"] < -1750,
        )
    elif case == "phase":
        checks.update(
            phase_two_entered=boss.get("phase_two") is True,
            crossed_health_threshold=finite(boss.get("health")) and 0 < boss["health"] <= expected_hp * 0.5,
            phase_observed=data.get("phase_observed") is True,
            transitioned_after_attack=boss.get("strikes", 0) >= 1,
            encounter_continues=data.get("engaged") is True and data.get("dead") is False,
        )
    elif case == "death":
        checks.update(natural_death=data.get("dead") is True and near(data.get("health"),0),multiple_boss_hits=data.get("damage_count",0)>=3,boss_not_dead=boss.get("state")!="dead")
    elif case == "victory":
        checks.update(
            victory=data.get("won") is True,
            enemy_dead=boss.get("state") == "dead" and near(boss.get("health"), 0),
            player_survived=data.get("dead") is False,
            encounter_stopped=data.get("engaged") is False,
            lock_released=data.get("locked") is False,
        )
    elif case == "retry":
        checks.update(
            actual_level_retry=data.get("retry_observed") is True,
            retry_completion_step=data.get("step") == 2,
            alive_after_retry=data.get("dead") is False and near(data.get("health"), 100),
            fresh_enemy=near(boss.get("health"), expected_hp) and boss.get("state") == "idle",
            encounter_reset=data.get("engaged") is False and data.get("locked") is False,
        )
    elif case == "input":
        checks.update(
            all_input_phases_exercised=finite(data.get("step")) and data["step"] >= 4,
            input_rules_valid=data.get("failures") == 0,
            attack_and_dodge_exercised=data.get("attacks", 0) >= 1 and data.get("dodges", 0) >= 1,
            final_idle=data.get("action") == "idle",
        )
    return checks


def write_json(path: Path, data: object) -> None:
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    temporary.replace(path)


def stop_owned_process(process: subprocess.Popen) -> dict:
    """The launcher uses exec, so this PID is the UE process that this case owns."""
    result = {"pid": process.pid, "terminated_by_harness": False, "killed_after_grace": False}
    if process.poll() is None:
        process.terminate()
        result["terminated_by_harness"] = True
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            result["killed_after_grace"] = True
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                result["cleanup_error"] = "Owned PID did not exit after SIGKILL."
    result["exit_code"] = process.poll()
    return result


def run_case(case: str, run_dir: Path, timeout: float, expected_hp: float, capture: bool = False, sample: bool = False, foot_placement: bool = False, terrain: str = "default", foot_audit: bool = False) -> dict:
    case_dir = run_dir / case
    case_dir.mkdir(parents=True)
    probe_file = OUTPUT / f"probe-{case}.json"
    screenshot_file = OUTPUT / f"{case}.png"
    # Preserve previous evidence instead of allowing a stale JSON to pass or deleting it.
    for source in (probe_file, screenshot_file):
        if source.exists():
            source.replace(case_dir / ("previous-" + source.name))
    marker = case_dir / "started.json"
    run_token = str(uuid.uuid4())
    write_json(marker, {"case": case, "run_token": run_token, "started_utc": dt.datetime.now(dt.timezone.utc).isoformat()})
    marker_ns = marker.stat().st_mtime_ns
    command = [str(ROOT / "Scripts/launch_mounted_boss.command"), f"-MountedProbe={case}",
               f"-MountedQARun={run_token}", f"-abslog={case_dir / 'engine.log'}"]
    if sample:command.append('-MountedChargeSample')
    if foot_placement:command.append('-MountedFootPlacement')
    if foot_audit:command.append('-MountedFootAudit')
    origins={'default':(0,0,0),'uphill':(0,800,-90),'downhill':(0,-800,90),'cross':(-800,0,0),'rock_edge':(-1450,650,0)}
    ox,oy,yaw=origins[terrain]
    command.extend([f'-MountedQAX={ox}',f'-MountedQAY={oy}',f'-MountedQAYaw={yaw}'])
    if capture:
        command.append("-MountedCapture")
        capture_dir=OUTPUT / "Capture" / case
        if capture_dir.exists():capture_dir.rename(case_dir / "previous-capture")
    process = None
    started = time.monotonic()
    data = None
    error = None
    malformed = None
    cleanup = {}
    try:
        with (case_dir / "stdout.log").open("w") as log:
            process = subprocess.Popen(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
            deadline = started + timeout
            while time.monotonic() < deadline:
                if probe_file.exists() and probe_file.stat().st_mtime_ns >= marker_ns:
                    try:
                        candidate = json.loads(probe_file.read_text())
                        if not isinstance(candidate, dict):
                            malformed = "Probe root was not a JSON object."
                        elif candidate.get("probe") != case:
                            malformed = "Fresh output named a different probe."
                        elif candidate.get("qa_run_id", run_token) != run_token:
                            malformed = "Fresh output belonged to another run."
                        elif candidate.get("complete") is True:
                            data = candidate
                            break
                    except (OSError, json.JSONDecodeError) as exc:
                        malformed = str(exc)
                if process.poll() is not None:
                    error = f"Owned UE process exited before a fresh completion (exit {process.returncode})."
                    break
                time.sleep(0.2)
            if data is None and error is None:
                error = f"No fresh completed fixture within {timeout:g} seconds."
                if malformed:
                    error += " Last output issue: " + malformed
            if data is not None:
                # RequestScreenshot is asynchronous; permit a short render without exceeding the case deadline.
                screenshot_deadline = min(deadline, time.monotonic() + 1.2)
                while not screenshot_file.exists() and process.poll() is None and time.monotonic() < screenshot_deadline:
                    time.sleep(0.1)
    except (OSError, ValueError) as exc:
        error = f"Could not run fixture: {exc}"
    finally:
        if process is not None:
            cleanup = stop_owned_process(process)
    engine_log_file = case_dir / "engine.log"
    engine_log = engine_log_file.read_text(errors="replace") if engine_log_file.exists() else ""
    result = {"case": case, "passed": False, "elapsed_seconds": round(time.monotonic() - started, 2),
              "evidence_directory": str(case_dir), "probe_path": str(probe_file), "process": cleanup}
    if data is not None:
        write_json(case_dir / "probe.json", data)
        checks = check_fixture(case, data, engine_log, expected_hp)
        if sample:
            checks['standard_sample_loaded']=data.get('boss',{}).get('standard_sample') is True
            if case in ('hit_charge','dodge_charge'):
                boss=data.get('boss',{})
                expected_seconds=json.loads((ROOT/'SourceAssets/MountedReferenceProduction/charge-timing.json').read_text())['phase_seconds']['end']
                checks['montage_finished_and_returned']=boss.get('state')=='approach' and near(boss.get('montage_time'),expected_seconds)
                checks['one_window_closed']=boss.get('window_begins')==1 and boss.get('window_ends')==1 and boss.get('notify_window') is False
                checks['six_beats_observed']=boss.get('phase_notifies')==6
                checks['horse_passed_player']=(boss.get('x',0)-ox)*math.cos(math.radians(yaw))+(boss.get('y',0)-oy)*math.sin(math.radians(yaw))>800
                checks['grounded_on_terrain']=boss.get('ground_supported') is True and near(boss.get('ground_clearance_cm'),0,.5)
        checks["engine_log_present"] = bool(engine_log)
        checks["owned_process_stopped"] = cleanup.get("exit_code") is not None
        result.update(checks=checks, passed=all(checks.values()), failed_checks=[k for k, v in checks.items() if not v])
        result["health"] = data.get("health")
        result["boss_health"] = data.get("boss", {}).get("health")
    if error:
        result["error"] = error
        result["passed"] = False
    if screenshot_file.exists() and screenshot_file.stat().st_mtime_ns >= marker_ns:
        import shutil
        shutil.copy2(screenshot_file, case_dir / "screenshot.png")
        result["screenshot_path"] = str(case_dir / "screenshot.png")
    if data is None and probe_file.exists() and probe_file.stat().st_mtime_ns >= marker_ns:
        import shutil
        shutil.copy2(probe_file, case_dir / "incomplete-probe.json")
    write_json(case_dir / "result.json", result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("cases", nargs="*", metavar="CASE")
    parser.add_argument("--all", action="store_true", help="Include movement, camera, lifecycle and input fixtures.")
    parser.add_argument("--timeout", type=float, default=90, help="Per-case UE completion deadline, at most 90 seconds.")
    parser.add_argument("--boss-health", type=float, default=900, help="Expected full Boss HP for this build.")
    parser.add_argument("--capture", action="store_true", help="Save timed native game frames for visual review.")
    parser.add_argument("--sample", action="store_true", help="Run unchanged fixtures against the opt-in standard-animation sample, with additional charge checks.")
    parser.add_argument("--foot-placement", action="store_true", help="Exercise the opt-in native four-limb Foot Placement candidate (requires --sample).")
    parser.add_argument("--foot-audit",action="store_true")
    parser.add_argument("--terrain",choices=["default","uphill","downhill","cross","rock_edge"],default="default")
    parser.add_argument("--list", action="store_true", help="List cases without starting UE.")
    args = parser.parse_args()
    if args.foot_placement and not args.sample:parser.error("--foot-placement requires --sample")
    available=ALL_CASES+(['sample_cleanup','sample_pre_cancel','shield_block'] if args.sample else [])
    if args.list:
        print("\n".join(available))
        return 0
    if any(case not in available for case in args.cases):
        parser.error("Unknown case(s): " + ", ".join(case for case in args.cases if case not in available))
    if not 0 < args.timeout <= 90:
        parser.error("--timeout must be greater than 0 and at most 90 seconds")
    if not math.isfinite(args.boss_health) or args.boss_health <= 0:
        parser.error("--boss-health must be a positive finite number")
    requested = args.cases or (available if args.all else DEFAULT_CASES)
    cases = []
    for case in requested:
        # A harmless roll alone is insufficient evidence: the same attack must hit
        # an undodging player in this run. Run its control first if needed.
        if case.startswith("dodge_"):
            control = "hit_" + case[6:]
            if control not in cases:
                cases.append(control)
        if case not in cases:
            cases.append(case)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    run_id = dt.datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:8]
    run_dir = OUTPUT / "runs" / run_id
    run_dir.mkdir(parents=True)
    report = {"run_id": run_id, "started_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
              "terrain":args.terrain,"expected_boss_health": args.boss_health, "requested_cases": cases, "results": [],
              "status": "running", "passed": False,
              "scope_note": "Runtime checks do not certify horse foot sliding, rider quality or camera occlusion."}
    try:
        for case in cases:
            result = run_case(case, run_dir, args.timeout, args.boss_health, args.capture,args.sample,args.foot_placement,args.terrain,args.foot_audit)
            if case.startswith("dodge_") and "checks" in result:
                control = next((item for item in report["results"] if item["case"] == "hit_" + case[6:]), None)
                result["checks"]["paired_hit_control_passed"] = bool(control and control["passed"])
                result["passed"] = result["passed"] and result["checks"]["paired_hit_control_passed"]
                result["failed_checks"] = [key for key, value in result["checks"].items() if not value]
                write_json(Path(result["evidence_directory"]) / "result.json", result)
            report["results"].append(result)
            print(json.dumps(result, ensure_ascii=False), flush=True)
            write_json(OUTPUT / "test-results.json", report)
            write_json(run_dir / "test-results.json", report)
    except KeyboardInterrupt:
        report["status"] = "interrupted"
        raise
    finally:
        if report["status"] == "running":
            report["status"] = "complete" if len(report["results"]) == len(cases) else "incomplete"
        report["passed"] = (report["status"] == "complete" and all(item["passed"] for item in report["results"]))
        report["finished_utc"] = dt.datetime.now(dt.timezone.utc).isoformat()
        write_json(OUTPUT / "test-results.json", report)
        write_json(run_dir / "test-results.json", report)
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
