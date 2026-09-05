"""Validate the scene actually loaded in UE, separate from source asset checks."""
import json
from pathlib import Path
import unreal as u
root=Path(__file__).resolve().parents[1]
ed=u.EditorAssetLibrary
actors=u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()
world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
report={'engine':u.SystemLibrary.get_engine_version(),'world':world.get_path_name(),'actors':[],
        'missing_materials':[],'missing_meshes':[],'rendering':{},'scope':'UE editor visual study with static figures; gameplay and performance not validated'}
for a in actors:
    name=a.get_actor_label()
    if not name.startswith(('AW_','AW2_')):continue
    p=a.get_actor_location()
    item={'name':name,'class':a.get_class().get_name(),'location_cm':[p.x,p.y,p.z]}
    if isinstance(a,u.StaticMeshActor):
        comp=a.static_mesh_component;mesh=comp.static_mesh
        if not mesh:report['missing_meshes'].append(name)
        else:
            item['mesh']=mesh.get_path_name()
            o,e=a.get_actor_bounds(False);item['center_cm']=[o.x,o.y,o.z];item['extent_cm']=[e.x,e.y,e.z]
            item['materials']=[]
            for i in range(comp.get_num_materials()):
                m=comp.get_material(i)
                item['materials'].append(m.get_path_name() if m else None)
                if not m:report['missing_materials'].append([name,i])
    report['actors'].append(item)
for name in ['r.DynamicGlobalIlluminationMethod','r.ReflectionMethod','r.GenerateMeshDistanceFields','r.RayTracing','r.ScreenPercentage']:
    report['rendering'][name]=u.SystemLibrary.get_console_variable_int_value(name)
report['static_mesh_actor_count']=sum(i['class']=='StaticMeshActor' for i in report['actors'])
report['v2_actor_count']=sum(i['name'].startswith('AW2_') for i in report['actors'])
report['passed']=not report['missing_materials'] and not report['missing_meshes'] and 'FirstDescentV02' in report['world'] and report['v2_actor_count']>=50
(root/'Saved/Automation/v2-verification.json').write_text(json.dumps(report,indent=2))
assert report['passed'],report
u.get_editor_subsystem(u.LevelEditorSubsystem).save_current_level()
u.log('ASHWELL V2 verification PASS: '+str(report['v2_actor_count'])+' V2 actors')
