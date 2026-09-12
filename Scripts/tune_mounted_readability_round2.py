"""Lighting / distant ground only, with a strict unchanged collision inventory.

No full arena rebuild. This edits the mounted map, not the Warden map.
"""
from pathlib import Path
import json,traceback,re
import os
import unreal as u
R=Path(__file__).resolve().parents[1];MAP='/Game/AshWell/MountedBoss/L_MountedCourtyard'
ED=u.EditorAssetLibrary;LE=u.get_editor_subsystem(u.LevelEditorSubsystem);AC=u.get_editor_subsystem(u.EditorActorSubsystem)
report={}
def stable_struct(value):
    # UObject Python wrappers include a transient allocation address in repr.
    return re.sub(r' \(0x[0-9a-fA-F]+\)', '', str(value))
def collision_inventory():
    records=[]
    for a in AC.get_all_level_actors():
        for c in a.get_components_by_class(u.PrimitiveComponent):
            if c.get_collision_enabled()==u.CollisionEnabled.NO_COLLISION:continue
            records.append({'actor':a.get_name(),'label':a.get_actor_label(),'component':c.get_name(),
                'actor_transform':stable_struct(a.get_actor_transform()),'relative_location':stable_struct(c.get_editor_property('relative_location')),
                'relative_rotation':stable_struct(c.get_editor_property('relative_rotation')),'relative_scale3d':stable_struct(c.get_editor_property('relative_scale3d')),
                'mode':str(c.get_collision_enabled()),'profile':str(c.get_collision_profile_name()),
                'object_type':str(c.get_collision_object_type()),'body':stable_struct(c.get_editor_property('body_instance')),
                'mesh':c.static_mesh.get_path_name() if isinstance(c,u.StaticMeshComponent) and c.static_mesh else None})
    return sorted(records,key=lambda x:(x['actor'],x['component']))
try:
    assert LE.load_level(MAP)
    before=collision_inventory();report['collision_before']=before
    actors={a.get_actor_label():a for a in AC.get_all_level_actors()}
    sun=actors['AWM_LateAfternoonSun'].light_component
    sky=actors['AWM_SkyFill'].light_component;fog=actors['AWM_DistanceHaze'].component
    report['before']={'sun':sun.get_editor_property('intensity'),'sky':sky.get_editor_property('intensity'),
                      'fog_density':fog.get_editor_property('fog_density')}
    sun.set_intensity(7.0);sun.set_light_color(u.LinearColor(1,.92,.80,1))
    sun.set_editor_property('light_source_angle',2.0)
    sky.set_intensity(1.6);sky.set_editor_property('lower_hemisphere_is_black',False)
    # Keep the existing specified ambient cubemap, which gives repeatable fill.
    fog.set_fog_density(.025);fog.set_fog_height_falloff(.12);fog.set_start_distance(1600)
    fog.set_fog_inscattering_color(u.LinearColor(.25,.29,.32,1))
    fog.set_fog_max_opacity(.85)
    # The old sky sphere's lower band stays black under the fixed exposure.
    # Use the engine atmosphere; retain the old actor hidden for an easy revert.
    if 'AWM_SkyBackdrop' in actors:
        actors['AWM_SkyBackdrop'].set_actor_hidden_in_game(True)
    if not any(isinstance(a,u.SkyAtmosphere) for a in actors.values()):
        atmosphere=AC.spawn_actor_from_class(u.SkyAtmosphere,u.Vector(0,0,-100))
        atmosphere.set_actor_label('AWM_Atmosphere');atmosphere.set_folder_path('MountedExperiment')
    sun.set_editor_property('atmosphere_sun_light',True)
    post=actors['AWM_FixedExposure'];settings=post.get_editor_property('settings')
    settings.set_editor_property('vignette_intensity',.08);post.set_editor_property('settings',settings)
    # Dedicated distant-scenery material: no shared floor material or collision edits.
    path='/Game/AshWell/MountedBoss/M_CourtyardDistantGroundRound2'
    mat=ED.load_asset(path) or u.AssetToolsHelpers.get_asset_tools().create_asset(path.rsplit('/',1)[1],path.rsplit('/',1)[0],u.Material,u.MaterialFactoryNew())
    ml=u.MaterialEditingLibrary;ml.delete_all_material_expressions(mat)
    color=ml.create_material_expression(mat,u.MaterialExpressionConstant3Vector);color.constant=u.LinearColor(.15,.16,.12,1)
    ml.connect_material_property(color,'',u.MaterialProperty.MP_BASE_COLOR)
    rough=ml.create_material_expression(mat,u.MaterialExpressionConstant);rough.r=.95;ml.connect_material_property(rough,'',u.MaterialProperty.MP_ROUGHNESS)
    ml.recompile_material(mat);ED.save_loaded_asset(mat)
    actors['AWM_DistantGround'].static_mesh_component.set_material(0,mat)
    after=collision_inventory();report['collision_after']=after
    report['collision_unchanged']=before==after
    assert before==after,'Refusing to save: collision inventory changed.'
    assert LE.save_current_level()
    report['after']={'sun':7,'sky':1.6,'fog_density':.025,'scope':'lighting, atmosphere, distant ground material only'}
    report['passed']=True
except Exception:
    report['passed']=False;report['error']=traceback.format_exc();u.log_error(report['error'])
finally:
    out=R/'Saved/MountedChargeRound2';out.mkdir(parents=True,exist_ok=True)
    (out/'readability.json').write_text(json.dumps(report,indent=2))
    u.log('ROUND2_READABILITY '+json.dumps({k:v for k,v in report.items() if not k.startswith('collision_')}))
    if os.environ.get('ASHWELL_ROUND2_CHAINED')!='1':u.SystemLibrary.quit_editor()
