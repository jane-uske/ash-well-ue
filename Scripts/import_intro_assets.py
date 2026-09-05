"""Import the original skinned animation and sound assets used by the intro."""
import json
from pathlib import Path
import unreal as u
ROOT=Path(__file__).resolve().parents[1]
ed=u.EditorAssetLibrary
tools=u.AssetToolsHelpers.get_asset_tools()
BASE='/Game/AshWell/Intro'
report={'skeletal_meshes':[],'animations':[],'sounds':[]}
def task(file,dest,name,opts=None,factory=None):
    t=u.AssetImportTask();t.filename=str(file);t.destination_path=dest;t.destination_name=name
    t.automated=True;t.replace_existing=True;t.save=True
    if opts:t.options=opts
    if factory:t.factory=factory
    tools.import_asset_tasks([t])
    paths=list(t.imported_object_paths)
    return ed.load_asset(dest+'/'+name),paths
src=ROOT/'SourceAssets/IntroCharacters'
for spec in json.loads((src/'manifest.json').read_text())['assets']:
    opts=u.FbxImportUI()
    for k,v in {'import_mesh':True,'import_as_skeletal':True,'import_materials':False,'import_textures':False,'import_animations':False,
                'create_physics_asset':False,'automated_import_should_detect_type':False,'mesh_type_to_import':u.FBXImportType.FBXIT_SKELETAL_MESH}.items():opts.set_editor_property(k,v)
    data=opts.skeletal_mesh_import_data
    for k,v in {'convert_scene':True,'convert_scene_unit':True,'force_front_x_axis':False,'import_uniform_scale':1.0,'normal_import_method':u.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS}.items():data.set_editor_property(k,v)
    mesh,paths=task(src/spec['skeletal_mesh'],BASE+'/Characters',spec['name'],opts,u.FbxFactory())
    assert mesh,spec['name']
    materials=list(mesh.get_editor_property('materials'))
    for i,m in enumerate(materials):
        slot=str(m.material_slot_name)
        name={'DarkSteel':'OldSteel'}.get(slot,slot)
        path='/Game/AshWell/Materials/'+(('M_'+name) if slot in ['Amber','Leather'] else 'V2/M_'+name)
        mat=ed.load_asset(path);assert mat,path
        m.set_editor_property('material_interface',mat)
        materials[i]=m
    mesh.set_editor_property('materials',materials);ed.save_loaded_asset(mesh)
    skeleton=mesh.get_editor_property('skeleton')
    report['skeletal_meshes'].append({'asset':mesh.get_path_name(),'skeleton':skeleton.get_path_name(),'paths':paths})
    for a in spec['animations']:
        opts=u.FbxImportUI()
        for k,v in {'import_mesh':False,'import_as_skeletal':True,'import_materials':False,'import_textures':False,'import_animations':True,'skeleton':skeleton,
                    'automated_import_should_detect_type':False,'mesh_type_to_import':u.FBXImportType.FBXIT_ANIMATION}.items():opts.set_editor_property(k,v)
        data=opts.anim_sequence_import_data
        for k,v in {'convert_scene':True,'convert_scene_unit':True,'force_front_x_axis':False,'import_uniform_scale':1.0,'use_default_sample_rate':True}.items():data.set_editor_property(k,v)
        anim,paths=task(src/a['file'],BASE+'/Characters',a['name'],opts,u.FbxFactory())
        if not anim:
            anim=next((ed.load_asset(p) for p in paths if isinstance(ed.load_asset(p),u.AnimSequence)),None)
            if anim:assert ed.rename_asset(anim.get_path_name(),BASE+'/Characters/'+a['name'])
            anim=ed.load_asset(BASE+'/Characters/'+a['name'])
        assert isinstance(anim,u.AnimSequence),str(paths)
        anim.set_editor_property('enable_root_motion',False);ed.save_loaded_asset(anim)
        report['animations'].append({'asset':anim.get_path_name(),'duration':anim.get_editor_property('sequence_length'),'expected':a['duration_seconds']})
src=ROOT/'SourceAssets/IntroAudio'
for a in json.loads((src/'manifest.json').read_text())['assets']:
    if 'Preview' in a['id']:continue
    sound,paths=task(src/a['file'],BASE+'/Audio',a['id'],factory=u.SoundFactory())
    assert isinstance(sound,u.SoundWave),str(paths)
    sound.set_editor_property('looping',a['looping'])
    ed.save_loaded_asset(sound)
    report['sounds'].append({'asset':sound.get_path_name(),'duration':a['duration_seconds'],'looping':a['looping']})
ed.save_directory(BASE,only_if_is_dirty=True,recursive=True)
(ROOT/'Saved/Automation/intro-assets-report.json').write_text(json.dumps(report,indent=2))
u.log('ASHWELL Intro animation/audio imported')
