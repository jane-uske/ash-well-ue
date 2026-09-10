#!/usr/bin/env python3
"""Bounded real-rendered UE probes; no simulation of reported results."""
import subprocess,time,json,pathlib,sys,os
R=pathlib.Path(__file__).resolve().parents[1];A=R/'Saved/Automation';OUT=R/'Saved/Polish';OUT.mkdir(exist_ok=True)
cases=sys.argv[1:] or ['slam','sweep','pursuit','dodge','invulnerability','stamina','ending','camera']
results=[]
for case in cases:
 f=A/f'probe-{case}.json'
 if f.exists():f.rename(f.with_suffix('.previous.json'))
 args=[str(R/'Scripts/launch_combat.command'),'-CombatQA',f'-WardenProbe={case}',f'-abslog={OUT}/probe-{case}.log']
 if case in ['slam','dodge','invulnerability']:args+=['-SingleStrike']
 with open(OUT/f'probe-{case}-stdout.log','w') as log:
  p=subprocess.Popen(args,stdout=log,stderr=subprocess.STDOUT,cwd=R)
  deadline=time.monotonic()+100
  while not f.exists() and time.monotonic()<deadline and p.poll() is None:time.sleep(.5)
  time.sleep(1.5)
  p.terminate()
  try:p.wait(15)
  except subprocess.TimeoutExpired:p.kill();p.wait()
 if not f.exists():results.append({'case':case,'pass':False,'error':'No completed fixture'});print(results[-1],flush=True);continue
 d=json.loads(f.read_text());checks={'completed':d['qa_complete'],'skinned':d['enemy_skinned_visual'],'animation':d['animation_blend_instance'],'weapon':d['polished_weapon']}
 if case=='slam':checks.update(health=d['health']==65,once=d['damage_taken_count']==1)
 if case=='sweep':checks.update(health=d['health']==40,once_per_strike=d['enemy_contacts']==2,kind=d['enemy_attack']=='sweep')
 if case=='pursuit':checks.update(health=d['health']==70,once=d['enemy_contacts']==1,kind=d['enemy_attack']=='pursuit')
 if case=='dodge':checks.update(unharmed=d['health']==100,dodged=d['dodges']==1)
 if case=='invulnerability':checks.update(unharmed=d['health']==100,evaded=d['evaded_hits']==1)
 if case=='stamina':checks.update(four_attacks=d['attacks']==4,cost=d['stamina']<24)
 if case=='ending':checks.update(record=d['record_read'],exit=d['slice_completed'])
 if case=='camera':checks.update(route=d['probe_step']==5,no_overlap=d['camera_overlap_seconds']==0)
 if case in ['slam','sweep','pursuit','dodge']:checks['committed_heading']=d['committed_yaw_drift']<.1
 results.append({'case':case,'pass':all(checks.values()),'checks':checks,'health':d['health'],'time':d['time']});print(results[-1],flush=True)
 (OUT/'runtime-probes.json').write_text(json.dumps(results,indent=2))
sys.exit(0 if all(x['pass'] for x in results) else 1)
