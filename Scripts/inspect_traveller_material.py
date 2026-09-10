import unreal as u,json
from pathlib import Path
ed=u.EditorAssetLibrary;L=u.MaterialEditingLibrary;B='/Game/AshWell/Combat/SwordPass';m=ed.load_asset(B+'/M_TravellerBody');r={}
for name,prop in [('base',u.MaterialProperty.MP_BASE_COLOR),('rough',u.MaterialProperty.MP_ROUGHNESS),('metal',u.MaterialProperty.MP_METALLIC),('normal',u.MaterialProperty.MP_NORMAL)]:
 n=L.get_material_property_input_node(m,prop);r[name]={'node':str(n),'texture':str(n.get_editor_property('texture')) if isinstance(n,u.MaterialExpressionTextureSample) else None}
mesh=ed.load_asset(B+'/SK_Traveller');r['materials']=[str(s.get_editor_property('material_interface')) for s in mesh.get_editor_property('materials')]
(Path(__file__).resolve().parents[1]/'Saved/SwordPass/material-inspect.json').write_text(json.dumps(r,indent=2))
report=r
