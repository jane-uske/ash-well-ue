"""Temporary PIE route driver, using native movement; no editor assets are changed."""
from pathlib import Path
import unreal as u,json,time,traceback
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'Saved/Terrace'
if hasattr(u,'_terrace_route_handle'):
 try:u.unregister_slate_post_tick_callback(u._terrace_route_handle)
 except Exception:pass
job=json.loads((OUT/'route-job.json').read_text());state={'id':job['id'],'status':'walking','index':0,'points':[],'errors':[]};started=time.monotonic();last=0;stuck=0;prev=None
world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_game_world();assert world and '/Terrace/' in world.get_path_name()
pawn=u.GameplayStatics.get_player_character(world,0);points=job['points'];u._terrace_route_state=state
state['default_speed']=pawn.character_movement.max_walk_speed
if 'test_speed' in job:pawn.character_movement.max_walk_speed=job['test_speed']
state['test_speed']=pawn.character_movement.max_walk_speed

def tick(dt):
 global last,stuck,prev
 try:
  p=pawn.get_actor_location();state['position']=[p.x,p.y,p.z]
  if p.z<100:raise RuntimeError('Below walkable floors')
  if state['index']>=len(points):
   pawn.character_movement.max_walk_speed=state['default_speed']
   state['status']='completed';u.unregister_slate_post_tick_callback(u._terrace_route_handle)
  else:
   x,y=points[state['index']];dist=((x-p.x)**2+(y-p.y)**2)**.5
   if dist<30:state['points'].append([p.x,p.y,p.z]);state['index']+=1;prev=None;stuck=0
   else:
    pawn.add_movement_input(u.Vector((x-p.x)/dist,(y-p.y)/dist,0),1,True)
    if prev and abs(p.x-prev[0])+abs(p.y-prev[1])<.03:stuck+=dt
    else:stuck=0
    prev=(p.x,p.y)
    if stuck>8:raise RuntimeError('Movement stalled at '+str(state['position']))
  if time.monotonic()-started>600:raise RuntimeError('Route timeout')
  if time.monotonic()-last>1 or state['status']=='completed':
   last=time.monotonic();(OUT/(job['id']+'.json')).write_text(json.dumps(state,indent=2))
 except Exception:
  state['status']='failed';state['errors'].append(traceback.format_exc());(OUT/(job['id']+'.json')).write_text(json.dumps(state,indent=2));u.unregister_slate_post_tick_callback(u._terrace_route_handle)
u._terrace_route_handle=u.register_slate_post_tick_callback(tick)
