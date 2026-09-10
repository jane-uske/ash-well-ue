#!/usr/bin/env python3
"""Evaluate real UE fixture outputs, including visual-failure telemetry (not art approval)."""
from pathlib import Path
import json,re,sys
R=Path(__file__).resolve().parents[1];A=R/'Saved/Automation';O=R/'Saved/SwordPass';checks=[]
def ck(name,value):checks.append({'check':name,'passed':bool(value)})
def vec(text):return [float(x) for x in re.findall(r'[XYZ]=([-\d.]+)',text)]
r=json.loads((A/'probe-sword_rules.json').read_text())
ck('zero-stamina light attacks, charged heavy/dodge and insufficient-resource rejection',r['probe_failures']==0 and r['probe_step']==9 and r['attacks']==7 and r['heavy_attacks']==1 and r['dodges']==1 and r['sword_pass'])
for i,(anim,speed) in enumerate([('Idle',0),('Walk',140),('Run',280),('Sprint',360),('Guard',0),('CombatWalk',155)]):
 d=json.loads((O/f'locomotion-{i}.json').read_text())
 expected=('A_Hero_'+('Meshy'+anim if anim in ['Walk','Run'] else anim)) if d.get('hero_complete_assets') else 'A_Sword_'+anim
 ck('locomotion '+anim,d['locomotion_animation']==expected and abs(d['speed']-speed)<4 and d['sword_pass'] and d['traveller_visual'] and d['grounded'])
 ck('human scale and material '+anim,vec(d['bone_head'])[2]>10 and d['skin_material']==('M_HeroBody' if d.get('hero_complete_assets') else 'M_TravellerBody'))
for i in range(5):
 d=json.loads((O/f'pose-{i}.json').read_text());h=vec(d['bone_hand_L']);t=vec(d['blade_tip']);distance=sum((x-y)**2 for x,y in zip(h,t))**.5
 ck('blade attached at pose '+str(i),distance<112 and d['skin_material']==('M_HeroBody' if d.get('hero_complete_assets') else 'M_TravellerBody'))
for case in ['battle_light','battle_heavy','battle_miss']:
 d=json.loads((A/f'probe-{case}.json').read_text());expected={'battle_light':760,'battle_heavy':745,'battle_miss':800}[case]
 ck(case,d['qa_complete'] and d['sword_pass'] and d['enemy_health']==expected and d['hits']==(0 if case=='battle_miss' else 1) and d['time_dilation']==1)
for case in ['battle_slam','battle_kick','battle_charge','battle_dodge_slam','battle_dodge_kick','battle_dodge_charge']:
 d=json.loads((A/f'probe-{case}.json').read_text());expected={'battle_slam':65,'battle_kick':80,'battle_charge':70}.get(case,100)
 ck(case,d['qa_complete'] and d['health']==expected and d['committed_yaw_drift']<.1)
for case in ['battle_camera','ending']:
 d=json.loads((A/f'probe-{case}.json').read_text())
 ck(case,d['qa_complete'] and (d['probe_step']==5 and d['camera_overlap_seconds']==0 if case=='battle_camera' else d['record_read'] and d['slice_completed'] and d['enemy_health']==0))
report={'passed':all(c['passed'] for c in checks),'checks':checks,'scope':'Actual runtime behaviour and pose-scale/attachment telemetry. Requires screenshot/video review for visual quality. No human playtest or long performance test claim.'}
(O/'sword-verification.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2));sys.exit(0 if report['passed'] else 1)
