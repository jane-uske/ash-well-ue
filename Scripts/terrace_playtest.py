"""Exercise native PIE collision and paths through CharacterMovement input, not position teleports."""
import unreal as u,json,time,traceback
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'Saved/Terrace';levels=u.get_editor_subsystem(u.LevelEditorSubsystem);engine=u.get_editor_subsystem(u.UnrealEditorSubsystem)
assert '/Terrace/' in engine.get_editor_world().get_path_name()
if levels.is_in_play_in_editor():raise RuntimeError('Existing PIE session is active; end this map session first.')
report={'status':'starting','waypoints':[],'errors':[]};(OUT/'playtest.json').write_text(json.dumps(report))
phase='waiting';last_write=0;started=time.monotonic();index=0;pc=None;pawn=None;stuck=0;previous=None
# First visit the front of the locked shortcut, then take the upper route to its back.
waypoints=[(-2300,0),(0,0),(1000,0),(0,0),(0,-2400),(3600,-2400),(3600,0),(1650,0)]
def tick(dt):
 global phase,last_write,index,pc,pawn,stuck,previous
 try:
  if time.monotonic()-started>600:raise RuntimeError('Playtest timed out')
  world=engine.get_game_world()
  if not world:return
  if pawn is None:
   pawn=u.GameplayStatics.get_player_character(world,0)
   if not pawn:return
   pc=u.GameplayStatics.get_player_controller(world,0);report['pawn']=pawn.get_class().get_path_name();report['initial_position']=str(pawn.get_actor_location());report['speed']=pawn.character_movement.max_walk_speed;phase='walking';report['status']='walking'
  p=pawn.get_actor_location()
  report['position']=[p.x,p.y,p.z];report['waypoint_index']=index;report['mode']=str(pawn.character_movement.movement_mode)
  if p.z < 100:raise RuntimeError('Player fell below the playable platforms')
  if index<len(waypoints):
   x,y=waypoints[index];dist=((x-p.x)**2+(y-p.y)**2)**.5
   if dist<55:
    report['waypoints'].append({'target':[x,y],'actual':[p.x,p.y,p.z]});index+=1;stuck=0;previous=None
   else:
    pawn.add_movement_input(u.Vector((x-p.x)/dist,(y-p.y)/dist,0),1,True)
    if previous is not None and abs(p.x-previous[0])+abs(p.y-previous[1])<.03:stuck+=dt
    else:stuck=0
    previous=(p.x,p.y)
    if stuck>8:raise RuntimeError('Native movement stuck approaching '+str((x,y))+' at '+str(report['position']))
  else:
   report['status']='at_gate_back';report['gate']=[{'open':a.get_editor_property('GateOpen'),'location':str(a.get_actor_location())} for a in u.GameplayStatics.get_all_actors_of_class(world,u.load_class(None,'/Game/AshWell/Terrace/BP_TerraceGate.BP_TerraceGate_C'))]
  if time.monotonic()-last_write>1:
   last_write=time.monotonic();(OUT/'playtest.json').write_text(json.dumps(report,indent=2))
 except Exception:
  report['status']='failed';report['errors'].append(traceback.format_exc());(OUT/'playtest.json').write_text(json.dumps(report,indent=2));u.unregister_slate_post_tick_callback(handle)
handle=u.register_slate_post_tick_callback(tick)
levels.editor_request_begin_play()
