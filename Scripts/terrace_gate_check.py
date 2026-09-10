from pathlib import Path
import unreal as u,json
root=Path(__file__).resolve().parents[1];world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_game_world();assert world and '/Terrace/' in world.get_path_name()
pc=u.GameplayStatics.get_player_controller(world,0);pawn=u.GameplayStatics.get_player_character(world,0);pc.set_control_rotation(u.Rotator(pitch=-5,yaw=180,roll=0))
gates=u.GameplayStatics.get_all_actors_of_class(world,u.load_class(None,'/Game/AshWell/Terrace/BP_TerraceGate.BP_TerraceGate_C'));g=gates[0]
(root/'Saved/Terrace/gate-check.json').write_text(json.dumps({'position':str(pawn.get_actor_location()),'gate':str(g.get_actor_location()),'open':g.get_editor_property('GateOpen'),'distance':pawn.get_distance_to(g),'world':world.get_path_name()},indent=2))
