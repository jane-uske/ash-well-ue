#!/usr/bin/env python3
"""Rendered UE fixtures: actual collision, damage, movement and real-time slowdown recovery."""
import subprocess,time,json,pathlib,sys
R=pathlib.Path(__file__).resolve().parents[1];O=R/'Saved/BattlePolish';O.mkdir(exist_ok=True);A=R/'Saved/Automation'
cases=sys.argv[1:] or ['battle_light','battle_heavy','battle_miss','battle_slam','battle_kick','battle_charge','battle_dodge_slam','battle_dodge_kick','battle_dodge_charge','battle_body','battle_wall','invulnerability','stamina']
results=[]
for case in cases:
 f=A/f'probe-{case}.json'
 if f.exists():f.rename(f.with_suffix('.previous.json'))
 with (O/f'{case}-stdout.log').open('w') as log:
  p=subprocess.Popen([str(R/'Scripts/launch_chapter01.command'),'-ChapterQA','-ChapterStationQA',f'-WardenProbe={case}',f'-abslog={O}/{case}.log'],stdout=log,stderr=subprocess.STDOUT,cwd=R)
  deadline=time.monotonic()+100
  while not f.exists() and time.monotonic()<deadline and p.poll() is None:time.sleep(.3)
  time.sleep(.8);p.terminate()
  try:p.wait(10)
  except subprocess.TimeoutExpired:p.kill();p.wait()
 if not f.exists():res={'case':case,'passed':False,'error':'No completed fixture'}
 else:
  d=json.loads(f.read_text());(O/f'{case}.json').write_text(json.dumps(d,indent=2));c={'complete':d['qa_complete'],'new_assets':d['battle_polish'],'speed_restored':d['time_dilation']==1}
  if case in ['battle_light','battle_heavy']:c.update(damage=d['enemy_health']==(760 if case=='battle_light' else 745),once=d['hits']==1,impact=d['fx_bursts']>0,slowdown_observed=d['minimum_dilation']<.5)
  if case=='battle_miss':c.update(no_damage=d['enemy_health']==800,no_hit=d['hits']==0,no_slowdown=d['minimum_dilation']==1)
  if case in ['battle_slam','battle_kick','battle_charge']:c.update(damage=d['health']=={'battle_slam':65,'battle_kick':80,'battle_charge':70}[case],once=d['damage_taken_count']==1,kind=d['enemy_attack']==case[7:],heading=d['committed_yaw_drift']<.1)
  if case.startswith('battle_dodge_'):c.update(unharmed=d['health']==100,dodged=d['dodges']==1,heading=d['committed_yaw_drift']<.1)
  if case=='hero_cloth':c.update(render_mapping=d['cloth_render_mappings']>0,solver_output=d['cloth_data_count']>0,wind_motion=d['cloth_motion_cm']>.05,stable=d['cloth_motion_cm']<20,free_hem=d['cloth_free_vertices']>100)
  if case=='hero_jump':c.update(jumped_once=d['jumps']==1,real_height=d['jump_peak_cm']>65,landed=d['grounded'],dodge_after_landing=d['dodges']==1,action_rules=d['probe_failures']==0,new_hero=d['hero_complete_assets'],jump_clip=d['jump_animation_loaded'],unit_scale=abs(d['hand_bone_scale']-1)<.01,cloth_solver=d['cloth_simulations']>0)
  if case=='battle_camera':c.update(five_positions=d['probe_step']==5,no_camera_penetration=d['camera_overlap_seconds']==0)
  if case=='battle_body':c.update(separated=d['minimum_separation']>=156.0,actually_approached=d['minimum_separation']<165)
  if case=='battle_wall':c.update(stopped=d['y']<=1295+1072.5-32,attempted_roll=d['dodges']==1,grounded=d['grounded'])
  if case=='invulnerability':c.update(unharmed=d['health']==100,evaded=d['evaded_hits']==1)
  if case=='stamina':c.update(four_attacks=d['attacks']==4,cost=d['stamina']<24)
  engine_log=(O/f'{case}.log').read_text(errors='replace')
  c['no_missing_assets']='LoadErrors: While trying to load package /Game/AshWell/Combat/HeroComplete' not in engine_log
  c['hero_material_compiles']='M_HeroBody.uasset: Failed to compile Material' not in engine_log
  c['cloth_scale_valid']='has a non uniform scale, and has a cloth simulation attached' not in engine_log
  res={'case':case,'passed':all(c.values()),'checks':c,'health':d['health'],'enemy_health':d['enemy_health'],'duration':d['time']}
 results.append(res);print(json.dumps(res),flush=True);(O/'runtime-probes.json').write_text(json.dumps(results,indent=2))
sys.exit(0 if all(r['passed'] for r in results) else 1)
