"""Create the playable 30-second intro in its own map; preserve visual V02."""
import json
from pathlib import Path
import unreal as u
root=Path(__file__).resolve().parents[1]
ed=u.EditorAssetLibrary
level=u.get_editor_subsystem(u.LevelEditorSubsystem)
actors=u.get_editor_subsystem(u.EditorActorSubsystem)
world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
assert 'FirstDescentIntro' in world.get_path_name(),world.get_path_name()
gm=u.load_class(None,'/Script/AshWell.AshWellIntroGameMode')
dc=u.load_class(None,'/Script/AshWell.AshWellIntroDirector')
assert gm and dc
world.get_world_settings().set_editor_property('default_game_mode',gm)
for a in actors.get_all_level_actors():
    name=a.get_actor_label()
    if name.startswith('AWIntro_') or name in ['AW2_SM_Expedition_Protagonist','AW2_SM_Expedition_Companion','AW_PlayerLantern','AW_CompanionLantern']:
        actors.destroy_actor(a)
start=actors.spawn_actor_from_class(u.PlayerStart,u.Vector(450,-60,89),u.Rotator(0,0,0))
start.set_actor_label('AWIntro_PlayerStart')
director=actors.spawn_actor_from_class(dc,u.Vector(1140,173,0))
director.set_actor_label('AWIntro_Director')
base='/Game/AshWell/Intro/'
for key,path in {
    'companion_mesh':'Characters/SK_Intro_Companion',
    'walk_animation':'Characters/A_Intro_Companion_Walk',
    'idle_animation':'Characters/A_Intro_Companion_Idle',
    'stop_animation':'Characters/A_Intro_Companion_StopSignal',
    'machinery_sound':'Audio/AW_Amb_MachineryLoop',
    'air_sound':'Audio/AW_Amb_WellAirLoop',
    'hush_sound':'Audio/AW_Foley_HushedBreath',
    'distant_metal_sound':'Audio/AW_Event_DistantLoadShift',
}.items():
    asset=ed.load_asset(base+path);assert asset,path;director.set_editor_property(key,asset)
director.set_editor_property('lantern_bone','lamp_light_L')
director.set_editor_property('visual_scale',u.Vector(1,-1,1))
visual=director.get_editor_property('companion_visual')
visual.set_skeletal_mesh_asset(ed.load_asset(base+'Characters/SK_Intro_Companion'))
visual.set_relative_scale3d(u.Vector(1,-1,1))
u.EditorLevelLibrary.set_level_viewport_camera_info(u.Vector(0,30,190),u.Rotator(pitch=-5,yaw=7,roll=0))
u.EditorLevelLibrary.editor_set_game_view(True)
level.save_current_level()
f=root/'Scripts/setup_intro_collision.py'
exec(compile(f.read_text(),str(f),'exec'),{'__file__':str(f),'__name__':'__main__'})
(root/'Saved/Automation/intro-map-report.json').write_text(json.dumps({'map':world.get_path_name(),'game_mode':gm.get_path_name(),'director':director.get_path_name(),'player_start_cm':[450,-60,89]},indent=2))
ed.save_directory('/Game/AshWell',only_if_is_dirty=True,recursive=True)
u.log('ASHWELL playable intro ready')
