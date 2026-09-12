import unreal as u,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];B='/Game/AshWell/Combat/MountedChargeSample/';report={}
for name in ['SK_SampleKnight','SK_SampleHorse']:
    m=u.EditorAssetLibrary.load_asset(B+name)
    report[name]={'bounds':str(m.get_bounds()),'skeleton':m.get_editor_property('skeleton').get_path_name(),
        'materials':[{'slot':str(s.material_slot_name),'material':s.material_interface.get_path_name() if s.material_interface else None} for s in m.get_editor_property('materials')]}
for name in ['M_SampleKnight','M_SampleHorse']:
    m=u.EditorAssetLibrary.load_asset(B+name)
    report[name]={'textures':[t.get_path_name() for t in u.MaterialEditingLibrary.get_used_textures(m)],'skeletal_usage':m.get_editor_property('used_with_skeletal_mesh')}
for name in ['SM_SamplePoleaxe','SM_SampleShield']:
    report[name]={'bounds':str(u.EditorAssetLibrary.load_asset(B+name).get_bounding_box())}
(R/'Saved/MountedChargeStandard/material-inspection.json').write_text(json.dumps(report,indent=2));u.log('SAMPLE_MATERIAL_INSPECTION '+json.dumps(report));u.SystemLibrary.quit_editor()
