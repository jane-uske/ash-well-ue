"""Read evaluated UE animation trajectories before adopting candidate gaits."""
from pathlib import Path
import unreal as u,json,statistics,traceback,os
R=Path(__file__).resolve().parents[1];B='/Game/AshWell/Combat/MountedChargeSample';report={}
try:
    for label in ['Idle','Walk','Gallop']:
        a=u.EditorAssetLibrary.load_asset(B+'/HorseRetargetConnected/A_IKSampleHorse_'+label);length=a.get_editor_property('sequence_length')
        feet={n:[] for n in ['Bone_046','Bone_052','Bone_025','Bone_031']}
        for frame in range(round(length*60)+1):
            p=u.AnimPoseExtensions.get_anim_pose_at_time(a,min(frame/60,length),u.AnimPoseEvaluationOptions())
            for name in feet:
                v=u.AnimPoseExtensions.get_bone_pose(p,name,u.AnimPoseSpaces.WORLD).translation
                feet[name].append([-v.y*1.3,-v.x*1.3,v.z*1.3])
        entry={};all_speeds=[]
        for name,points in feet.items():
            ground=min(v[2] for v in points);speeds=[-(b[0]-a[0])*60 for a,b in zip(points,points[1:]) if max(a[2],b[2])<ground+3 and -(b[0]-a[0])*60>20]
            entry[name]={'min_z_cm':ground,'max_z_cm':max(v[2] for v in points),'support_speed':statistics.median(speeds) if speeds else None,'support_samples':len(speeds)};all_speeds+=speeds
        report[label]={'hooves':entry,'median_support_speed_cm_s':statistics.median(all_speeds) if all_speeds else None,'duration':length}
except Exception:report['error']=traceback.format_exc()
(R/'Saved/MountedChargeStandard/ue-ik-gait-audit.json').write_text(json.dumps(report,indent=2));u.log('IK_GAIT_AUDIT '+json.dumps(report))
if os.environ.get('ASHWELL_ADOPT_IK_GAITS')=='1':
    assert 'error' not in report,report
    for label in ['Walk','Gallop']:
        for hoof in report[label]['hooves'].values():
            assert hoof['min_z_cm']>=-1 and hoof['max_z_cm']-hoof['min_z_cm']>8,(label,hoof)
    os.environ['ASHWELL_SAMPLE_GRAPH_ONLY']='1';os.environ['ASHWELL_SAMPLE_IK_GAITS']='1'
    script=R/'Scripts/import_mounted_charge_sample.py'
    exec(compile(script.read_text(),str(script),'exec'),{'__file__':str(script),'__name__':'__main__'})
else:u.SystemLibrary.quit_editor()
