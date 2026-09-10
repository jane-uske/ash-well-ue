#!/usr/bin/env python3
"""Retain unchanged player rules against the pinned baseline, plus new runtime reports.
The old visual-only guard remains available; it intentionally rejects new Boss rules.
"""
import json
from pathlib import Path
import verify_warden_gameplay as old
R=Path(__file__).resolve().parents[1]
base=old.tokens(old.git('show',f'{old.BASELINE}:{old.PLAYER}'));now=old.tokens((R/old.PLAYER).read_text())
checks=[]
for name in ['ToggleLock','IsInvulnerable','InputDirection','MoveForwardCombat','MoveRightCombat','SlowDown','SlowUp','IsDead','HasWon','ShouldUpdateLocomotion']:
 checks.append(old.check('unchanged player '+name,old.body(base,'AAshWellCombatCharacter',name),old.body(now,'AAshWellCombatCharacter',name)))
# Preserve action durations/displacement, stamina recovery, costs, and invulnerability.
for snippet in ['Stamina+26*Dt','StateTime>=.8333f','StateTime>=.5833f','StateTime>=.45f','570.f*FMath::Sin(FMath::Clamp(StateTime/.5833f,0.f,1.f)*PI)','StateTime>=.23f&&StateTime<=.43f','ActionDirection*(100*Dt)']:
 t=old.tokens(snippet);contains=lambda x:any(x[i:i+len(t)]==t for i in range(len(x)-len(t)+1))
 checks.append({'check':'retained '+snippet,'passed':contains(base) and contains(now)})
report={'baseline':old.BASELINE,'passed':all(c['passed'] for c in checks),'checks':checks,'scope':'Unchanged input, invulnerability, locomotion and action timings. Attack/Dodge/UpdateAttack/TakeDamage now intentionally support Heavy and impact feedback; validate those through test_battle_runtime.py, not byte-identical legacy function bodies.'}
(R/'Saved/Polish/player-invariants.json').write_text(json.dumps(report,indent=2))
print(json.dumps({'passed':report['passed'],'count':len(checks),'failures':[c['check'] for c in checks if not c['passed']]},indent=2))
raise SystemExit(0 if report['passed'] else 1)
