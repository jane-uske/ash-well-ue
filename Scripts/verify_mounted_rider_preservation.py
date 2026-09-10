"""Verify the mounted trim preserves every limb vertex/weight and every bone.
Runs only in disposable background Blender and does not change source assets."""
import bpy,json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];O=R/'SourceAssets/MountedBoss'
bpy.ops.wm.open_mainfile(filepath=str(O/'MountedRiderPrepared.blend'));new=bpy.data.objects['SK_MountedRider'];newrig=bpy.data.objects['WardenRig']
with bpy.data.libraries.load(str(R/'SourceAssets/WardenRig/WardenRig.blend'),link=False) as (src,dst):dst.objects=['SK_WardenRig','WardenRig']
old=next(o for o in dst.objects if o.type=='MESH');oldrig=next(o for o in dst.objects if o.type=='ARMATURE')
def sig(o):
 names={g.index:g.name for g in o.vertex_groups};out=[]
 for v in o.data.vertices:
  w={names[g.group]:g.weight for g in v.groups}
  if w.get('Body',0)>.999:continue
  out.append((tuple(round(c,6) for c in v.co),tuple(sorted((k,round(v,6)) for k,v in w.items()))))
 return sorted(out)
a,b=sig(old),sig(new)
err=max(abs(oldrig.data.bones[n].matrix_local[i][j]-newrig.data.bones[n].matrix_local[i][j]) for n in oldrig.data.bones.keys() for i in range(4) for j in range(4))
report={'all_non_body_vertex_positions_and_weights_preserved':a==b,'non_body_vertex_count_before':len(a),'non_body_vertex_count_after':len(b),'bone_rest_max_error':err,'bone_names_preserved':list(oldrig.data.bones.keys())==list(newrig.data.bones.keys()),'original_source_sha256_unchanged':hashlib.sha256((R/'SourceAssets/WardenRig/WardenRig.blend').read_bytes()).hexdigest()==json.loads((O/'mounted_rider_manifest.json').read_text())['source_sha256']}
assert a==b and err<1e-6 and report['bone_names_preserved'] and report['original_source_sha256_unchanged'],report
(O/'mounted-rider-preservation.json').write_text(json.dumps(report,indent=2));print(report)
