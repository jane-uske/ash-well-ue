"""Reproduce the mounted rider leg IK and inspect the stirrup/sole alignment.
Background asset assembly only; upper-body attack pose and UE runtime animation
are intentionally not represented and cannot be validated by this image."""
import bpy,math,json
from pathlib import Path
from mathutils import Vector,Matrix
R=Path(__file__).resolve().parents[1];O=R/'SourceAssets/MountedBoss';j=json.loads((R/'SourceAssets/WardenHQ/warden_manifest.json').read_text());J={n:Vector(v) for n,v in j['blender_rh_joints_cm'].items()}
bpy.ops.wm.open_mainfile(filepath=str(O/'MountedHorsePrepared.blend'));s=bpy.context.scene;rig=bpy.data.objects['MountedHorseRig'];a=bpy.data.actions['A_Horse_Idle'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];s.frame_set(1)
with bpy.data.libraries.load(str(O/'MountedRiderPrepared.blend'),link=False) as (src,dst):dst.objects=[n for n in src.objects if n in ('WardenRig','SK_MountedRider')]
for o in dst.objects:s.collection.objects.link(o)
rider=next(o for o in dst.objects if o.type=='ARMATURE')
with bpy.data.libraries.load(str(O/'MountedProps.blend'),link=False) as (src,dst):dst.objects=['SM_MountedSaddle']
seat=dst.objects[0];s.collection.objects.link(seat);seat.hide_render=False;seat.location=(0,0,175);seat.scale=(1,1,.925)
M=Matrix.Translation((0,0,103.6))@Matrix.Scale(.68,4)
bpy.context.view_layer.update()
def limb(A,B,C,desired,hint):
 U=(B-A).length;L=(C-B).length;D=(desired-A).length;direction=(desired-A).normalized();bend=(hint-direction*hint.dot(direction)).normalized();along=(U*U-L*L+D*D)/(2*D);return A+direction*along+bend*math.sqrt(U*U-along*along),desired

def link(A,B,C,D):
 Q=(B-A).rotation_difference(D-C);m=Q.to_matrix().to_4x4();m.translation=C-Q@A;return m
report={}
for side,sign in [('Right',-1),('Left',1)]:
 A,B,C=[J[side+x] for x in ['Hip','Knee','Ankle']];desired=Vector((20,sign*63,38));K,E=limb(A,B,C,desired,Vector((1,sign*.25,0)))
 rider.pose.bones[side+'Thigh'].matrix=link(A,B,A,K)@rider.data.bones[side+'Thigh'].matrix_local;rider.pose.bones[side+'Shin'].matrix=link(B,C,K,E)@rider.data.bones[side+'Shin'].matrix_local;rider.pose.bones[side+'Foot'].matrix=Matrix.Translation(E-C)@rider.data.bones[side+'Foot'].matrix_local
 report[side]={'hip_cm':list(M@A),'knee_cm':list(M@K),'ankle_cm':list(M@E),'inside_knee_degrees':math.degrees((A-K).angle(E-K)), 'target_distance_cm':(E-A).length,'available_leg_cm':(B-A).length+(C-B).length}
rider.matrix_world=M
# Source props material positions align to the actual UE imported centimetres.
for n,d in json.loads((O/'horse_manifest.json').read_text())['materials'].items():
 m=bpy.data.materials.get(n)
 if m:m.use_nodes=True;m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=d['base_color'];m.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.68
bpy.ops.mesh.primitive_plane_add(size=2000,location=(0,0,-1));g=bpy.context.object;m=bpy.data.materials.new('Ground');m.diffuse_color=(.04,.05,.06,1);g.data.materials.append(m)
for loc,power in [((200,-280,450),1200000),((-350,250,400),700000)]:
 bpy.ops.object.light_add(type='AREA',location=loc);l=bpy.context.object;l.data.energy=power;l.data.shape='DISK';l.data.size=350;l.rotation_euler=(Vector((0,0,140))-l.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add(location=(20,-600,185));c=bpy.context.object;c.rotation_euler=(Vector((0,0,145))-c.location).to_track_quat('-Z','Y').to_euler();c.data.type='ORTHO';c.data.ortho_scale=360;s.camera=c
s.render.engine='BLENDER_EEVEE';s.render.resolution_x=1200;s.render.resolution_y=1000;s.render.resolution_percentage=100;s.view_settings.view_transform='AgX';s.render.image_settings.file_format='PNG';s.render.filepath=str(O/'mounted-rider-trim-diagnostic.png');bpy.ops.render.render(write_still=True)
(O/'mounted-rider-seat-verification.json').write_text(json.dumps(report,indent=2));print('SEAT_CHECK',json.dumps(report))
