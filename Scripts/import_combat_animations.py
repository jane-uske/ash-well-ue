"""Import original combat FBX clips onto the existing Intro protagonist skeleton.

Run from the UE editor Python session. Does not replace the existing mesh or clips.
"""
import json
from pathlib import Path
import unreal as u

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'SourceAssets/CombatCharacters'
BASE='/Game/AshWell/Combat/Characters'
manifest=json.loads((SRC/'manifest.json').read_text())
ed=u.EditorAssetLibrary
tools=u.AssetToolsHelpers.get_asset_tools()
skeleton=ed.load_asset(manifest['skeleton'])
assert isinstance(skeleton,u.Skeleton),manifest['skeleton']
report={'skeleton':skeleton.get_path_name(),'animations':[]}
for clip in manifest['animations']:
    opts=u.FbxImportUI()
    for k,v in {'import_mesh':False,'import_as_skeletal':True,'import_materials':False,
                'import_textures':False,'import_animations':True,'skeleton':skeleton,
                'automated_import_should_detect_type':False,
                'mesh_type_to_import':u.FBXImportType.FBXIT_ANIMATION}.items():
        opts.set_editor_property(k,v)
    data=opts.anim_sequence_import_data
    for k,v in {'convert_scene':True,'convert_scene_unit':True,'force_front_x_axis':False,
                'import_uniform_scale':1.0,'use_default_sample_rate':False,
                'custom_sample_rate':60}.items():data.set_editor_property(k,v)
    task=u.AssetImportTask()
    task.filename=str(SRC/clip['file']);task.destination_path=BASE
    task.destination_name=clip['name'];task.automated=True;task.replace_existing=True
    task.save=True;task.options=opts;task.factory=u.FbxFactory()
    tools.import_asset_tasks([task])
    paths=list(task.imported_object_paths)
    anim=ed.load_asset(BASE+'/'+clip['name'])
    if not anim:
        anim=next((ed.load_asset(p) for p in paths if isinstance(ed.load_asset(p),u.AnimSequence)),None)
        if anim:assert ed.rename_asset(anim.get_path_name(),BASE+'/'+clip['name'])
        anim=ed.load_asset(BASE+'/'+clip['name'])
    assert isinstance(anim,u.AnimSequence),(clip['name'],paths)
    anim.set_editor_property('enable_root_motion',False)
    duration=anim.get_editor_property('sequence_length')
    assert abs(duration-clip['duration_seconds'])<.02,(clip['name'],duration)
    assert anim.get_editor_property('skeleton')==skeleton,clip['name']
    ed.save_loaded_asset(anim)
    report['animations'].append({'asset':anim.get_path_name(),'duration':duration,
                                'expected':clip['duration_seconds'],'root_motion':False})
ed.save_directory(BASE,only_if_is_dirty=True,recursive=True)
(ROOT/'Saved/Automation').mkdir(exist_ok=True,parents=True)
(ROOT/'Saved/Automation/combat-animations-report.json').write_text(json.dumps(report,indent=2)+'\n')
u.log('ASHWELL Combat animations imported')
