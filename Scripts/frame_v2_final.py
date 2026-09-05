from pathlib import Path
import unreal as u
root=Path(__file__).resolve().parents[1]
source=(root/'Scripts/build_v2_materials.py').read_text()
exec(compile(source.split("src=ROOT/'SourceAssets/SurfaceV2'")[0],str(root/'Scripts/build_v2_materials.py'),'exec'))
src=ROOT/'SourceAssets/Textures'
concrete=next(s for s in json.loads((src/'manifest.json').read_text())['materials'] if s['material_name']=='M_Concrete')
pbr('RoomConcrete',src,concrete,.75,(.20,.22,.22),.80,.64,.25,macro=True)
roommat=ed.load_asset('/Game/AshWell/Materials/V2/M_RoomConcrete')
actors=u.get_editor_subsystem(u.EditorActorSubsystem)
for a in actors.get_all_level_actors():
    name=a.get_actor_label()
    if name.startswith('AW2_Scan_Right_'):
        p=a.get_actor_location();a.set_actor_location(u.Vector(p.x,580,p.z),False,False)
    if name.startswith('AW2_SM_DeepCrossing_'):
        a.set_actor_location(u.Vector(0,0,600),False,False)
    if name.startswith('AW2_Practical_LowerBridge_'):
        p=a.get_actor_location();a.set_actor_location(u.Vector(p.x,p.y,-1478),False,False)
    if name.startswith('AW2_SM_AV2_ServiceRooms_'):
        mesh=a.static_mesh_component.static_mesh
        for i,s in enumerate(mesh.get_editor_property('static_materials')):
            if str(s.material_slot_name)=='Concrete':a.static_mesh_component.set_material(i,roommat)
u.get_editor_subsystem(u.LevelEditorSubsystem).save_current_level()
