from pathlib import Path
import bpy,json
R=Path(__file__).resolve().parents[1];O=R/'meshy_output/20260909_battle_motion_v01'
report={}
for name in ['Slash','Hammer','Kick','Roll','Hit']:
 scene=bpy.data.scenes.new('AW_Source_'+name);bpy.context.window.scene=scene
 before=set(bpy.data.objects);bpy.ops.import_scene.fbx(filepath=str(O/(name+'.fbx')));new=set(bpy.data.objects)-before
 rig=next(o for o in new if o.type=='ARMATURE');rig.name='AW_SourceRig_'+name;act=rig.animation_data.action;end=round(act.frame_range[1]);samples=[]
 for f in range(1,end+1):
  scene.frame_set(f);samples.append({'frame':f,'bones':{b.name:{'head':list(rig.matrix_world@b.head),'tail':list(rig.matrix_world@b.tail),'matrix':[list(row) for row in (rig.matrix_world@b.matrix)]} for b in rig.pose.bones}})
 report[name]={'rig':rig.name,'scene':scene.name,'fps':scene.render.fps,'range':[1,end],'samples':samples}
(O/'source-motion-samples.json').write_text(json.dumps(report))
bpy.ops.wm.save_as_mainfile(filepath=str(O/'MotionSources.blend'))
result={n:{'frames':v['range'],'fps':v['fps'],'samples':[{k:s['bones'][k]['head'] for k in ['Hips','LeftHand','RightHand','LeftFoot','RightFoot']} for s in v['samples'][::15]]} for n,v in report.items()}
