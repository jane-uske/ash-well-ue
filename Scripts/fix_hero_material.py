from pathlib import Path
import unreal as u
R=Path(__file__).resolve().parents[1]
code=(R/'Scripts/import_hero_complete.py').read_text().split("skeleton=None;report={}")[0]
exec(compile(code,str(R/'Scripts/import_hero_complete.py'),'exec'))
u.log('HERO_MATERIAL_FIXED')
import json
m=u.EditorAssetLibrary.load_asset('/Game/AshWell/Combat/HeroComplete/SK_HeroCloak')
a=m.get_editor_property('mesh_clothing_assets')[0]
r={'configs':str(a.get_editor_property('cloth_configs'))}
l=a.get_editor_property('lod_data')[0];p=l.get_editor_property('physical_mesh_data');v=p.get_editor_property('vertices')
r['vertices']=len(v);r['min']=[min(getattr(x,k) for x in v) for k in ['x','y','z']];r['max']=[max(getattr(x,k) for x in v) for k in ['x','y','z']]
r['masks']=[{'target':x.get_editor_property('current_target'),'enabled':x.get_editor_property('enabled'),'range':[min(x.get_editor_property('values')),max(x.get_editor_property('values'))]} for x in l.get_editor_property('point_weight_maps')]
(R/'Saved/HeroComplete/cloth-inspect.json').write_text(json.dumps(r,indent=2))
