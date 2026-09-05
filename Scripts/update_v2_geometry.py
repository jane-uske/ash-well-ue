"""Reimport the seven revised architecture chunks without resetting the map."""
from pathlib import Path
import json
import unreal as u
root=Path(__file__).resolve().parents[1]
lev=u.get_editor_subsystem(u.LevelEditorSubsystem)
world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
doc={'world':world.get_path_name(),'subsystem':{n:str(getattr(lev,n).__doc__) for n in dir(lev) if 'save' in n},'utils':{n:str(getattr(u.EditorLoadingAndSavingUtils,n).__doc__) for n in dir(u.EditorLoadingAndSavingUtils) if 'save' in n}}
(root/'Saved/Automation/v2-save-api.json').write_text(json.dumps(doc,indent=2))
del world
ed=u.EditorAssetLibrary
tools=u.AssetToolsHelpers.get_asset_tools()
actors=u.get_editor_subsystem(u.EditorActorSubsystem)
byname={a.get_actor_label():a for a in actors.get_all_level_actors()}
categories={'ArchitectureV2':['SM_AV2_ServiceRooms_0','SM_AV2_ServiceRooms_1','SM_AV2_ServiceRooms_2','SM_AV2_Windows_And_Lamps'],
            'ArchitectureV2/Foreground':['SM_AV2_FG_LayeredSteel','SM_AV2_FG_PipeJoints','SM_AV2_FG_CablesAndDrips'],
            'SurfaceV2/DeepCrossing':['SM_DeepCrossing_Bridge','SM_DeepCrossing_WorkersAndLamps']}
cachefile=root/'Saved/Automation/v2-import-cache.json'
cache=json.loads(cachefile.read_text())
for cat,names in categories.items():
    for name in names:
        file=root/'SourceAssets'/cat/(name+'.fbx')
        dest='/Game/AshWell/Meshes/'+cat
        key=str(file.relative_to(root))
        if cache.get(key)==file.stat().st_mtime_ns and 'AW2_'+name in byname:continue
        task=u.AssetImportTask();task.filename=str(file);task.destination_path=dest;task.destination_name=name
        task.automated=True;task.replace_existing=True;task.save=True
        opts=u.FbxImportUI()
        for k,v in {'import_mesh':True,'import_as_skeletal':False,'import_materials':False,'import_textures':False,
                    'automated_import_should_detect_type':False,'mesh_type_to_import':u.FBXImportType.FBXIT_STATIC_MESH}.items():opts.set_editor_property(k,v)
        for k,v in {'combine_meshes':True,'convert_scene':True,'convert_scene_unit':True,'force_front_x_axis':False,
                    'transform_vertex_to_absolute':True,'generate_lightmap_u_vs':False,'auto_generate_collision':False,
                    'normal_import_method':u.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS}.items():opts.static_mesh_import_data.set_editor_property(k,v)
        task.options=opts;task.factory=u.FbxFactory();tools.import_asset_tasks([task])
        mesh=ed.load_asset(dest+'/'+name);assert mesh
        a=byname.get('AW2_'+name)
        if not a:
            a=actors.spawn_actor_from_class(u.StaticMeshActor,u.Vector(0,0,0))
            a.set_actor_label('AW2_'+name);a.set_actor_scale3d(u.Vector(1,-1,1))
        a.static_mesh_component.set_static_mesh(mesh)
        for i,s in enumerate(mesh.get_editor_property('static_materials')):
            slot=str(s.material_slot_name)
            path='/Game/AshWell/Materials/'+({'Amber':'M_Amber','Rock':'M_Rock','Leather':'M_Leather'}.get(slot,'V2/M_'+{'DarkSteel':'OldSteel'}.get(slot,slot)))
            mat=ed.load_asset(path)
            if mat:a.static_mesh_component.set_material(i,mat)
        cache[str(file.relative_to(root))]=file.stat().st_mtime_ns
cachefile.write_text(json.dumps(cache,indent=2))
u.get_editor_subsystem(u.LevelEditorSubsystem).save_current_level()
