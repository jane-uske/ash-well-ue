"""Import the detailed V2 geometry into a separate, editable Unreal level."""
import json
from pathlib import Path
import unreal as u
ROOT=Path(__file__).resolve().parents[1]
BASE='/Game/AshWell'
MAP=BASE+'/Maps/FirstDescentV02Final'
ed=u.EditorAssetLibrary
tools=u.AssetToolsHelpers.get_asset_tools()
level=u.get_editor_subsystem(u.LevelEditorSubsystem)
actors=u.get_editor_subsystem(u.EditorActorSubsystem)
if ed.does_asset_exist(MAP):level.load_level(MAP)
else:
    level.load_level(BASE+'/Maps/FirstDescent')
    # Save Map As uses the editor world lifecycle; asset duplication leaves a
    # standalone UWorld that prevents subsequent level loading on UE 5.7.
    world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    assert u.EditorLoadingAndSavingUtils.save_map(world,MAP)
    del world
    import gc
    gc.collect()
    level.load_level(MAP)

remove=['AW_SM_ColossalPier','AW_SM_CivicHall','AW_SM_DistantAccessBridges','AW_SM_Expedition',
        'AW_SM_WalkwayDeck','AW_SM_MineRock_Left','AW_SM_MineRock_Right','AW_SM_MineRoof','AW_SM_SideCliffLower','AW2_']
for a in actors.get_all_level_actors():
    if any(a.get_actor_label().startswith(n) for n in remove):actors.destroy_actor(a)
materials={n:ed.load_asset(BASE+'/Materials/M_'+n) for n in ['Rock','Concrete','Amber','Leather']}
materials.update({n:ed.load_asset(BASE+'/Materials/V2/M_'+m) for n,m in {
    'Cloth':'Cloth','Canvas':'Canvas','Rust':'Rust','DarkSteel':'OldSteel','WetStone':'WetStone','Debris':'Debris'}.items()})
assert all(materials.values())
report={'map':MAP,'imports':[],'missing_slots':[]}
cachefile=ROOT/'Saved/Automation/v2-import-cache.json'
cache=json.loads(cachefile.read_text()) if cachefile.exists() else {}
def import_mesh(file,category):
    destpath=BASE+'/Meshes/'+category
    name=file.stem;assetpath=destpath+'/'+name
    mesh=ed.load_asset(assetpath);key=str(file.relative_to(ROOT))
    if not mesh or cache.get(key)!=file.stat().st_mtime_ns:
        task=u.AssetImportTask();task.filename=str(file);task.destination_path=destpath;task.destination_name=name
        task.automated=True;task.replace_existing=True;task.save=True
        opts=u.FbxImportUI()
        for k,v in {'import_mesh':True,'import_as_skeletal':False,'import_materials':False,'import_textures':False,
                    'automated_import_should_detect_type':False,'mesh_type_to_import':u.FBXImportType.FBXIT_STATIC_MESH}.items():opts.set_editor_property(k,v)
        for k,v in {'combine_meshes':True,'convert_scene':True,'convert_scene_unit':True,'force_front_x_axis':False,
                    'transform_vertex_to_absolute':True,'generate_lightmap_u_vs':False,'auto_generate_collision':False,
                    'normal_import_method':u.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS}.items():opts.static_mesh_import_data.set_editor_property(k,v)
        task.options=opts;task.factory=u.FbxFactory();tools.import_asset_tasks([task]);mesh=ed.load_asset(assetpath)
        assert mesh,assetpath
        cache[key]=file.stat().st_mtime_ns
        cachefile.write_text(json.dumps(cache,indent=2))
    report['imports'].append(assetpath)
    return mesh
def meshactor(name,mesh,pos=(0,0,0),rot=(0,0,0),scale=(1,-1,1),override=None):
    a=actors.spawn_actor_from_class(u.StaticMeshActor,u.Vector(*pos),u.Rotator(pitch=rot[0],yaw=rot[1],roll=rot[2]))
    a.set_actor_label('AW2_'+name);a.set_actor_scale3d(u.Vector(*scale))
    comp=a.static_mesh_component;comp.set_static_mesh(mesh);comp.set_mobility(u.ComponentMobility.STATIC)
    for i,smat in enumerate(mesh.get_editor_property('static_materials')):
        slot=str(smat.material_slot_name)
        found=override or materials.get(slot)
        if found:comp.set_material(i,found)
        else:report['missing_slots'].append([name,slot])
    return a

for cat in ['ArchitectureV2','ArchitectureV2/Foreground','SurfaceV2','SurfaceV2/DeepCrossing','CharactersV2']:
    for f in sorted((ROOT/'SourceAssets'/cat).glob('*.fbx')):
        a=meshactor(f.stem,import_mesh(f,cat))
        if cat=='CharactersV2':a.set_actor_location(u.Vector(450,170 if 'Companion' in f.stem else 0,0),False,False)

# The photographed rock scans keep their original nonrepeating UVs.
scanmeshes={}
for aid in ['rock_face_01','boulder_01']:
    f=ROOT/'SourceAssets/ScansV2/Prepared'/({'rock_face_01':'SM_Scan_RockFace01.fbx','boulder_01':'SM_Scan_Boulder01_LOD0.fbx'}[aid])
    if not f.exists():raise RuntimeError('Prepared scan missing: '+str(f))
    scanmeshes[aid]=import_mesh(f,'ScansV2')
def rock(name,aid,pos,rot=(0,0,0),scale=(1,1,1)):
    mat=ed.load_asset(BASE+'/Materials/V2/M_Scan_'+aid)
    return meshactor(name,scanmeshes[aid],tuple(v*100 for v in pos),rot,(scale[0],-scale[1],scale[2]),mat)
import random
rng=random.Random(312)
for i,x in enumerate([-2,3.5,9,14.5]):
    rock('Scan_Left_Low_'+str(i),'rock_face_01',(x,-2.9,-.45),(0,180+rng.uniform(-4,4),0),(1.05,1,1.15))
    rock('Scan_Left_High_'+str(i),'rock_face_01',(x-1,-3.8,4.1),(0,174+rng.uniform(-7,7),2),(1.15,1.1,1.45))
for i,x in enumerate([-3,3]):
    rock('Scan_Right_'+str(i),'rock_face_01',(x,3.8,-.6),(0,0,0),(1,1.1,1.3))
for i,(x,y,z,s) in enumerate([(1,-2,3.9,3),(5,-2.3,4.7,3),(2,1.5,5,3),(-2,0,4.6,3),(8,-2,5.5,4)]):
    rock('Scan_Roof_'+str(i),'boulder_01',(x,y,z),(rng.uniform(-20,20),rng.uniform(0,360),rng.uniform(-15,15)),(s*1.5,s,s*.8))
for i,(x,y,z) in enumerate([(12,-7,-9),(18,-9,-17),(7,-8,-8),(20,-13,-32),(5,-12,-25)]):
    rock('Scan_LowerCliff_'+str(i),'rock_face_01',(x,y,z),(0,165+rng.uniform(-10,10),3),(2.5,2,3))
for i in range(24):
    x=rng.uniform(-.5,17);y=-1.52-rng.uniform(0,.65);s=rng.uniform(.13,.5)
    rock('Scan_EdgeStone_'+str(i),'boulder_01',(x,y,-s*.13),(0,rng.uniform(0,360),0),(s,s,s*.65))

names={a.get_actor_label():a for a in actors.get_all_level_actors()}
for name in ['AW_SM_MineSteelFrames','AW_SM_MinePipesAndCables','AW_SM_WalkwayRails','AW_SM_WalkwayEdgeBeams','AW_SM_WalkwayUnderTruss']:
    a=names.get(name)
    if a:
        for i,s in enumerate(a.static_mesh_component.static_mesh.get_editor_property('static_materials')):
            if str(s.material_slot_name) in materials:a.static_mesh_component.set_material(i,materials[str(s.material_slot_name)])
camera=names['AW_HeroCamera']
camera.set_actor_location(u.Vector(0,30,190),False,False)
camera.set_actor_rotation(u.Rotator(pitch=-5,yaw=7,roll=0),False)
camera.camera_component.set_editor_property('field_of_view',70.0)
names['AW_PlayerLantern'].set_actor_location(u.Vector(457,-25.4537,67.4),False,False)
names['AW_CompanionLantern'].set_actor_location(u.Vector(1146.2578,95.8303,67.4),False,False)
names['AW_PlayerLantern'].light_component.set_intensity(270)
names['AW_CompanionLantern'].light_component.set_intensity(220)
names['AW_PlayerFill'].light_component.set_intensity(600)
u.EditorLevelLibrary.set_level_viewport_camera_info(camera.get_actor_location(),camera.get_actor_rotation())
u.EditorLevelLibrary.editor_set_game_view(True)
level.save_current_level();ed.save_directory(BASE,only_if_is_dirty=True,recursive=True)
(ROOT/'Saved/Automation/v2-scene-report.json').write_text(json.dumps(report,indent=2))
u.log('ASHWELL V2 scene assembled')
