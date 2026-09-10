"""Build only /Game/AshWell/Terrace. Original maps, gameplay source and assets are read-only."""
from pathlib import Path
import unreal as u, math, json, random
from editor_toolset.toolsets.blueprint import BlueprintTools as B
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'Saved/Terrace';BASE='/Game/AshWell/Terrace';MAP=BASE+'/L_BrokenChainTerrace'
ed=u.EditorAssetLibrary;assets=u.AssetToolsHelpers.get_asset_tools();levels=u.get_editor_subsystem(u.LevelEditorSubsystem);actors=u.get_editor_subsystem(u.EditorActorSubsystem)
assert not levels.is_in_play_in_editor()
if ed.does_asset_exist(MAP):
 assert levels.load_level(MAP)
 for a in actors.get_all_level_actors():
  assert a.get_actor_label().startswith('AWT_') or isinstance(a,(u.WorldSettings,u.LevelScriptActor)),a.get_actor_label()
  if a.get_actor_label().startswith('AWT_'):actors.destroy_actor(a)
else: assert levels.new_level(MAP)
world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world();assert world.get_path_name().startswith(MAP)
count=0
V=lambda x,z,h:u.Vector(-z*100,x*100,h*100)
def spawn(cls,name,pos,rot=None,folder='Terrace/Playable'):
 global count
 count+=1;a=actors.spawn_actor_from_class(cls,pos,rot or u.Rotator());a.set_actor_label('AWT_'+name+'_'+str(count));a.set_folder_path(folder);return a
cube=ed.load_asset('/Engine/BasicShapes/Cube.Cube');cylinder=ed.load_asset('/Engine/BasicShapes/Cylinder.Cylinder');sphere=ed.load_asset('/Engine/BasicShapes/Sphere.Sphere')
M={k:ed.load_asset(path) for k,path in {'steel':'/Game/AshWell/Materials/V2/M_OldSteel','rust':'/Game/AshWell/Materials/V2/M_Rust','stone':'/Game/AshWell/Materials/V2/M_Concrete','rock':'/Game/AshWell/Materials/M_Rock','dark':'/Game/AshWell/Materials/M_DarkSteel','floor':'/Game/AshWell/Materials/V2/M_WetStone','glow':'/Game/AshWell/Materials/M_Amber'}.items()}
assert all(M.values())
def flatmat(name,color,emissive=0):
 mat=ed.load_asset(BASE+'/'+name) or assets.create_asset(name,BASE,u.Material,u.MaterialFactoryNew());m=u.MaterialEditingLibrary;m.delete_all_material_expressions(mat)
 c=m.create_material_expression(mat,u.MaterialExpressionConstant3Vector);c.constant=u.LinearColor(*color,1);m.connect_material_property(c,'',u.MaterialProperty.MP_BASE_COLOR)
 if emissive:
  e=m.create_material_expression(mat,u.MaterialExpressionConstant3Vector);e.constant=u.LinearColor(*(x*emissive for x in color),1);m.connect_material_property(e,'',u.MaterialProperty.MP_EMISSIVE_COLOR)
 m.recompile_material(mat);ed.save_loaded_asset(mat);return mat
M['lamp']=flatmat('M_TerraceLamp',(1,.46,.12),9)
M['mark']=flatmat('M_TerraceMark',(.65,.46,.19))
def static(name,mesh,pos,scale,mat,rot=None,collision=True,folder='Terrace/Playable'):
 a=spawn(u.StaticMeshActor,name,pos,rot,folder);c=a.static_mesh_component;c.set_static_mesh(mesh);a.set_actor_scale3d(u.Vector(*scale))
 if mat:c.set_material(0,mat)
 c.set_collision_profile_name('BlockAll' if collision else 'NoCollision');return a
def box(name,x,z,h,w,d,t,mat='steel',yaw=0,collision=True,folder='Terrace/Playable'):
 return static(name,cube,V(x,z,h),(d,w,t),M[mat],u.Rotator(pitch=0,yaw=yaw,roll=0),collision,folder)
def beam(name,a,b,r=.06,mat='rust',collision=True,folder='Terrace/Playable'):
 aa=V(a[0],a[1],a[2]);bb=V(b[0],b[1],b[2]);delta=bb-aa
 return static(name,cylinder,(aa+bb)*.5,(r*2,r*2,delta.length()/100),M[mat],u.MathLibrary.make_rot_from_z(delta),collision,folder)
def lamp(x,z,h):
 box('Lamp',x,z,h,.24,.24,.2,'lamp',collision=False)
 a=spawn(u.PointLight,'WarmLight',V(x,z,h-.12));c=a.point_light_component;c.set_intensity(650);c.set_attenuation_radius(850);c.set_light_color(u.LinearColor(1,.48,.19,1));c.set_editor_property('cast_shadows',False)
def shared_detail(name,path,center,scale,materials):
 mesh=ed.load_asset(path);assert mesh,path
 b=mesh.get_bounding_box();c=(b.min+b.max)*.5;s=u.Vector(*scale)
 a=static(name,mesh,center-u.Vector(c.x*s.x,c.y*s.y,c.z*s.z),scale,None,collision=False,folder='Terrace/SharedDetails')
 for i in range(len(mesh.get_editor_property('static_materials'))):a.static_mesh_component.set_material(i,materials[i%len(materials)])
 return a
# Only sign textures authored for this map are imported.
signs={}
for png in (ROOT/'SourceAssets/Terrace/Signs').glob('*.png'):
 dest=BASE+'/Signs/T_'+png.stem
 if not ed.does_asset_exist(dest):
  task=u.AssetImportTask();task.filename=str(png);task.destination_path=BASE+'/Signs';task.destination_name='T_'+png.stem;task.automated=True;task.save=True;assets.import_asset_tasks([task])
 tex=ed.load_asset(dest);mat=ed.load_asset(BASE+'/Signs/M_'+png.stem) or assets.create_asset('M_'+png.stem,BASE+'/Signs',u.Material,u.MaterialFactoryNew());m=u.MaterialEditingLibrary;m.delete_all_material_expressions(mat)
 sample=m.create_material_expression(mat,u.MaterialExpressionTextureSample);sample.texture=tex;m.connect_material_property(sample,'RGB',u.MaterialProperty.MP_BASE_COLOR);m.connect_material_property(sample,'RGB',u.MaterialProperty.MP_EMISSIVE_COLOR);m.recompile_material(mat);ed.save_loaded_asset(mat);signs[png.stem]=mat
plane=ed.load_asset('/Engine/BasicShapes/Plane.Plane')
def sign(name,x,z,h,w=4,yaw=180):
 p=V(x,z,h)
 a=static('Sign_'+name,plane,p+u.Vector(1,0,0),(w,w/4,1),signs[name],u.Rotator(pitch=0,yaw=-90,roll=90),False)
 static('SignBack_'+name,plane,p-u.Vector(1,0,0),(w,w/4,1),signs[name],u.Rotator(pitch=0,yaw=90,roll=90),False)
 return a
# Separate Blueprint game mode; read-only reuse of the existing explorer and controls.
walker=ed.load_asset(BASE+'/BP_TerraceWalker') or B.create(BASE,'BP_TerraceWalker',u.load_class(None,'/Script/AshWell.AshWellIntroCharacter'))
B.compile_blueprint(walker);cdo=B.get_default_object(walker)
cdo.character_movement.set_editor_property('max_walk_speed',90);cdo.character_movement.set_editor_property('max_acceleration',700);cdo.character_movement.set_editor_property('braking_deceleration_walking',700)
boom=cdo.get_editor_property('camera_boom');boom.set_editor_property('do_collision_test',True);boom.set_editor_property('target_arm_length',450);boom.set_editor_property('socket_offset',u.Vector(0,60,102));ed.save_loaded_asset(walker)
gm=ed.load_asset(BASE+'/BP_TerraceGameMode') or B.create(BASE,'BP_TerraceGameMode',u.GameModeBase.static_class());B.compile_blueprint(gm);gcdo=B.get_default_object(gm)
gcdo.set_editor_property('default_pawn_class',walker.generated_class());gcdo.set_editor_property('player_controller_class',u.load_class(None,'/Script/AshWell.AshWellIntroPlayerController'));gcdo.set_editor_property('hud_class',u.HUD.static_class());ed.save_loaded_asset(gm)
world.get_world_settings().set_editor_property('default_game_mode',gm.generated_class())
spawn(u.PlayerStart,'Start',V(0,23,16.95),u.Rotator(pitch=0,yaw=0,roll=0))
# Real floor meshes and physical rails. x/z plan coordinates are metres; Unreal uses centimetres.
paths=[('Exit',(0,29,16),(0,0,16),9),('UpperA',(0,0,16),(-24,0,16),7),('UpperB',(-24,0,16),(-24,-36,16),7),('UpperC',(-24,-36,16),(0,-36,16),8),('LowerA',(0,0,16),(18,0,16),7),('Down',(18,0,16),(26,-12,8),6),('LowerHall',(26,-12,8),(26,-36,8),6),('Up',(26,-36,8),(12,-48,16),6),('LowerEnd',(12,-48,16),(0,-36,16),7),('Shortcut',(0,-36,16),(0,0,16),5.5)]
for name,a,b,w in paths:
 aa=V(*a);bb=V(*b);delta=bb-aa;length=delta.length()/100;rot=u.MathLibrary.find_look_at_rotation(aa,bb);mid=(aa+bb)*.5;mid.z-=22
 floor=static('Floor_'+name,cube,mid,(length+.1,w,.44),M['floor'],rot)
 dx=b[0]-a[0];dz=b[1]-a[1];horizontal=math.hypot(dx,dz);nx=dz/horizontal;nz=-dx/horizontal
 for d in range(4,int(horizontal)-3,4):
  f=d/horizontal;x=a[0]+dx*f;z=a[1]+dz*f;y=a[2]+(b[2]-a[2])*f
  for s in [-1,1]:beam('RailPost',(x+nx*(w/2-.1)*s,z+nz*(w/2-.1)*s,y),(x+nx*(w/2-.1)*s,z+nz*(w/2-.1)*s,y+1.15),.055)
  if d%8==0:
   box('Support',x,z,y-10,.65,.8,19.5,'dark');beam('Brace',(x+nx*w/2,z+nz*w/2,y-.25),(x,z,y-4),.12)
 for s in [-1,1]:
  for height in [.55,1.1]:
   cut=7 if name=='Exit' else 4;f1=cut/horizontal;f2=(horizontal-cut)/horizontal
   if f2>f1:beam('Rail',(a[0]+dx*f1+nx*(w/2-.1)*s,a[1]+dz*f1+nz*(w/2-.1)*s,a[2]+(b[2]-a[2])*f1+height),(a[0]+dx*f2+nx*(w/2-.1)*s,a[1]+dz*f2+nz*(w/2-.1)*s,a[2]+(b[2]-a[2])*f2+height),.045)
for x,z,r in [(0,0,8.5),(0,-36,8),(-24,-36,5)]:static('Landing',cylinder,V(x,z,15.7),(r*2,r*2,.6),M['floor'])
# Short enclosed exit creates the first reveal.
for x in [-4.75,4.75]:box('LiftWall',x,24,19,.7,12,6,'dark')
box('LiftRoof',0,24,22,10,12,.6,'dark');box('LiftBack',0,29.5,19,10,.6,6,'dark')
for x in [-4.3,4.3]:beam('LiftFrame',(x,18,16),(x,18,21.7),.13)
box('LiftHeader',0,18,21.7,9,.4,.3,'rust');lamp(-3.8,23,19.5);sign('entry',0,18.8,20.4,6)
# Reference the existing mine entrance steelwork, preserving the source asset.
shared_detail('SharedEntranceSteel','/Game/AshWell/Meshes/ArchitectureV2/Foreground/SM_AV2_FG_LayeredSteel',V(0,24,18.5),(1,1,1),[M['steel'],M['rust']])
for x,z,y in [(-6,3,16),(-25,3,16),(-25,-30,16),(23,-15,8),(28,-29,8),(3,-39,16)]:
 beam('LampPole',(x,z,y),(x,z,y+3.6),.075);lamp(x,z,y+3.5)
sign('routes',-4,-4,18.1,4.4);sign('crane',-21,-35,18.4,3.8);sign('gate',0,-13,20.6,3.8);sign('lower',26,-14,11.4,4)
# The lower maintenance gallery is eight metres below the open upper walkway.
for x in [22.65,29.35]:box('GalleryWall',x,-24,10.5,.55,21,5,'dark')
box('GalleryRoof',26,-24,13,7.3,21,.4,'dark')
for z in [-15,-20,-25,-30,-34]:
 for x in [22.95,29.05]:beam('GalleryFrame',(x,z,8),(x,z,12.7),.09)
 box('GalleryLintel',26,z,12.7,6.3,.2,.2,'rust')
for x in [23.35,23.75]:beam('UtilityPipe',(x,-13,11.8),(x,-34,11.8),.15,'steel')
shared_detail('SharedPipeJoints','/Game/AshWell/Meshes/ArchitectureV2/Foreground/SM_AV2_FG_PipeJoints',V(26,-24,12.05),(1.8,.7,.65),[M['steel'],M['rust']])
# Static supplies and a broken crane, with room to move around its base.
for x,z,y,w,d in [(-26,-20,16,1,3),(27.8,-27,8,1,2.5),(-3.5,-38.5,16,3.2,3.2)]:
 box('Crate',x,z,y+.6,w,d,1.2,'rust')
 for yy in [.12,1.05]:box('CrateBand',x,z,y+yy,w+.03,d+.03,.06,'steel')
for dx in [-1,1]:
 for dz in [-1,1]:beam('CraneLeg',(-3.5+dx,-38.5+dz,16),(-3.5+dx*.65,-38.5+dz*.65,35),.18)
for y in range(18,35,4):
 box('CraneRing',-3.5,-38.5,y,2.3,2.3,.22,'rust');beam('CraneCross',(-4.5,-39.5,y),(-2.5,-39.5,y+3.8),.08)
beam('BrokenBoom',(-3.5,-38.5,34.5),(-17,-54,39),.3);beam('BrokenBoomLower',(-3.5,-38.5,32),(-17,-54,37),.22)
for i in range(8):
 t=i/8;tt=(i+1)/8;beam('BoomWeb',(-3.5-13.5*t,-38.5-15.5*t,34.5+4.5*t),(-3.5-13.5*tt,-38.5-15.5*tt,32+5*tt),.08)
beam('CounterweightArm',(-3.5,-38.5,35),(5,-31,36),.25);box('Counterweight',5,-31,34.5,3.5,3,3,'dark');beam('HangingChain',(-15,-51,38),(-15,-51,23),.1,'dark')
# Gate logic is a saved native Blueprint, not an editor-only Python behaviour.
gatebp=ed.load_asset(BASE+'/BP_TerraceGate');g=B.get_graph(gatebp,'EventGraph')
code=r'''(event EventTick (DeltaSeconds)
 (if (not (Variables|Default|GetGateOpen))
  (bind player (Game|GetPlayerCharacter :PlayerIndex 0))
  (Utilities|IsValid :InputObject player
   (:"Is Valid"
    (bind loc (Transformation|GetActorLocation :self self))
    (bind ploc (Transformation|GetActorLocation :self player))
    (if (and (< (Transformation|GetDistanceTo :self self :OtherActor player) 390.0) (> (.x ploc) (.x loc)))
     (bind pc (Game|GetPlayerController :PlayerIndex 0))
     (if (Game|Player|WasInputKeyJustPressed :self pc :Key "E")
      (Variables|Default|SetGateOpen true)
      (Collision|SetActorEnableCollision :self self :bNewActorEnableCollision false)
      (Transformation|SetActorLocation :self self :NewLocation (Math|Vector|MakeVector (.x loc) (.y loc) (+ (.z loc) 420.0)))
      (Development|PrintString :InString "SHORTCUT OPEN - return to the lift" :Duration 5.0))))
   (:"Is Not Valid"))))'''
B.write_graph_dsl(g,code);ed.save_loaded_asset(gatebp)
gate=spawn(gatebp.generated_class(),'ReturnGate',V(0,-13,17.8));gate.static_mesh_component.set_mobility(u.ComponentMobility.MOVABLE);gate.static_mesh_component.set_static_mesh(cube);gate.static_mesh_component.set_material(0,M['rust']);gate.static_mesh_component.set_collision_profile_name('BlockAll');gate.set_actor_scale3d(u.Vector(.22,5.5,3.6))
for x in [-2.9,2.9]:box('GateFrame',x,-13,18,.3,.45,4,'rust')
box('GateHeader',0,-13,20,6,.4,.25,'rust')
# Distant landscape is a composition guide, beyond this map's walkable area.
box('BasinFloor',30,-180,-61,650,650,5,'rock',folder='Terrace/Far')
rng=random.Random(81)
# Engine primitives carry the distant terrain masses in this graybox.
for i in range(26):
 side=-1 if i%2 else 1;x=side*rng.uniform(80,230);z=rng.uniform(-360,-40);h=rng.uniform(-35,0)
 a=static('RockMass',sphere,V(x,z,h),(rng.uniform(35,60),rng.uniform(35,60),rng.uniform(60,125)),M['rock'],u.Rotator(pitch=rng.uniform(-20,20),yaw=rng.uniform(0,180),roll=10),False,'Terrace/Far')
scan=ed.load_asset('/Game/AshWell/Meshes/ScansV2/SM_Scan_Boulder01_LOD0');scanmat=ed.load_asset('/Game/AshWell/Materials/V2/M_Scan_boulder_01')
for i,(x,z,h,s) in enumerate([(20,5,-5,20),(-22,9,-2,15),(35,-32,-6,12)]):
 static('SharedScannedRock',scan,V(x,z,h),(s,s,s),scanmat,u.Rotator(pitch=0,yaw=i*73,roll=0),False,'Terrace/SharedDetails')
box('HomeRockShelf',-108,-178,29,154,79,112,'rock',folder='Terrace/Far/Home');box('HomeFoundation',-104,-176,87,154,83,8,'dark',folder='Terrace/Far/Home')
for i in range(10):box('HomePier',-168+i*14,-133,40,3.8,5,98,'stone',folder='Terrace/Far/Home')
for y in [-2,24,51,77]:box('HomeGallery',-104,-130,y,150,4,1.4,'steel',folder='Terrace/Far/Home')
for i in range(18):
 x=-166+(i%9)*14;z=-149-(i//9)*22;h=rng.uniform(13,28)
 box('HomeBlock',x,z,92+h/2,11,17,h,'dark',folder='Terrace/Far/Home');box('HomeRoof',x,z,92+h+.5,12,18,1,'steel',folder='Terrace/Far/Home')
 for row in range(4):
  for col in range(2):
   if rng.random()>.2:box('HomeWindow',x-3+col*5,z+8.6,95+row*4,.9,.15,1.5,'lamp',collision=False,folder='Terrace/Far/Home')
box('RationTower',-96,-166,111,10,10,38,'stone',folder='Terrace/Far/Home');box('RationCrown',-96,-166,130,19,17,4,'steel',folder='Terrace/Far/Home');beam('HomeAerial',(-96,-166,132),(-96,-166,145),.18,folder='Terrace/Far/Home')
beam('FurnaceCarcass',(35,-153,-28),(118,-199,-12),15,'rust',False,'Terrace/Far/Furnace')
for i in range(8):
 x=rng.uniform(30,125);z=rng.uniform(-200,-135);box('FurnaceRuin',x,z,-44,8,10,15,'dark',rng.uniform(0,45),False,'Terrace/Far/Furnace')
box('RidgeMass',145,-295,25,90,75,145,'rock',collision=False,folder='Terrace/Far/Ridge')
for x in [139,151]:beam('MastLeg',(x,-281,92),(145,-283,143),.6,folder='Terrace/Far/Ridge')
for y in range(98,138,8):beam('MastCross',(139,-281,y),(151,-281,y+7),.2,folder='Terrace/Far/Ridge')
beam('Aerial',(128,-283,130),(168,-283,130),.35,'steel',False,'Terrace/Far/Ridge');beam('AerialTip',(145,-283,143),(145,-283,158),.16,folder='Terrace/Far/Ridge');box('MastBeacon',145,-283,158,.9,.9,.9,'lamp',collision=False,folder='Terrace/Far/Ridge')
# Lumen lighting and physical sky, authored only in this new level.
sun=spawn(u.DirectionalLight,'SkyKey',u.Vector(0,0,8000),u.Rotator(pitch=-24,yaw=-45,roll=0),'Terrace/Lighting');sun.get_component_by_class(u.DirectionalLightComponent).set_intensity(3.5);sun.get_component_by_class(u.DirectionalLightComponent).set_light_color(u.LinearColor(.64,.79,1,1));sun.get_component_by_class(u.DirectionalLightComponent).set_editor_property('atmosphere_sun_light',True)
sky=spawn(u.SkyAtmosphere,'Atmosphere',u.Vector(0,0,-6000),folder='Terrace/Lighting')
skylight=spawn(u.SkyLight,'SkyFill',u.Vector(0,0,6000),folder='Terrace/Lighting');skylight.get_component_by_class(u.SkyLightComponent).set_editor_property('real_time_capture',True);skylight.get_component_by_class(u.SkyLightComponent).set_intensity(.65)
fog=spawn(u.ExponentialHeightFog,'DepthFog',u.Vector(0,0,-1500),folder='Terrace/Lighting');fog.get_component_by_class(u.ExponentialHeightFogComponent).set_editor_property('fog_density',.016);fog.get_component_by_class(u.ExponentialHeightFogComponent).set_editor_property('fog_height_falloff',.16);fog.get_component_by_class(u.ExponentialHeightFogComponent).set_editor_property('fog_inscattering_luminance',u.LinearColor(.16,.23,.29,1));fog.get_component_by_class(u.ExponentialHeightFogComponent).set_editor_property('start_distance',2200)
pp=spawn(u.PostProcessVolume,'Exposure',u.Vector(0,0,0),folder='Terrace/Lighting');pp.set_editor_property('unbound',True);s=pp.settings
for key,value in [('override_auto_exposure_min_brightness',True),('override_auto_exposure_max_brightness',True),('auto_exposure_min_brightness',.6),('auto_exposure_max_brightness',.6),('override_motion_blur_amount',True),('motion_blur_amount',0.)]:s.set_editor_property(key,value)
pp.settings=s
assert levels.save_current_level();ed.save_directory(BASE,only_if_is_dirty=True,recursive=True)
u.get_editor_subsystem(u.UnrealEditorSubsystem).set_level_viewport_camera_info(V(0,9,19),u.Rotator(pitch=5,yaw=-7,roll=0))
report={'ok':True,'map':MAP,'actors':count,'playable_paths':paths,'gate':gate.get_path_name(),'game_mode':gm.generated_class().get_path_name(),'source_boundary':'Only new Terrace map, Blueprints, signs and helper scripts written. Existing source, maps and assets untouched.'}
(OUT/'build-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));u.log('TERRACE BUILD COMPLETE')
