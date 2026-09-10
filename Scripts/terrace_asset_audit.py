"""Read existing shared assets, write only the Terrace verification record."""
from pathlib import Path
import unreal as u,json
from editor_toolset.toolsets.blueprint import BlueprintTools as B
root=Path(__file__).resolve().parents[1];out=root/'Saved/Terrace';ed=u.EditorAssetLibrary
bp=ed.load_asset('/Game/AshWell/Terrace/BP_TerraceGate')
(out/'gate-dsl-fixed.txt').write_text(B.read_graph_dsl(B.get_graph(bp,'EventGraph')))
paths=['/Game/AshWell/Meshes/ScansV2/SM_Scan_Boulder01_LOD0','/Game/AshWell/Meshes/ScansV2/SM_Scan_RockFace01','/Game/AshWell/Meshes/ArchitectureV2/Foreground/SM_AV2_FG_LayeredSteel','/Game/AshWell/Meshes/ArchitectureV2/Foreground/SM_AV2_FG_PipeJoints']
report=[]
for path in paths:
 mesh=ed.load_asset(path)
 if not mesh:continue
 b=mesh.get_bounding_box();mn=b.min;mx=b.max
 report.append({'path':path,'min':[mn.x,mn.y,mn.z],'max':[mx.x,mx.y,mx.z],'materials':[str(s.material_interface.get_path_name()) if s.material_interface else None for s in mesh.get_editor_property('static_materials')]})
(out/'shared-mesh-audit.json').write_text(json.dumps(report,indent=2))
