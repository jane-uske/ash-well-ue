"""Create only the independent outdoor mounted experiment; never load a baseline map."""
from pathlib import Path
import unreal as u,math,json
R=Path(__file__).resolve().parents[1];B='/Game/AshWell/MountedBoss';MAP=B+'/L_MountedCourtyard'
ed=u.EditorAssetLibrary;at=u.AssetToolsHelpers.get_asset_tools();le=u.get_editor_subsystem(u.LevelEditorSubsystem);ac=u.get_editor_subsystem(u.EditorActorSubsystem);ml=u.MaterialEditingLibrary
ed.make_directory(B)
assert not le.is_in_play_in_editor()
if ed.does_asset_exist(MAP):assert le.load_level(MAP)
else:assert le.new_level(MAP)
world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world();assert world.get_path_name().startswith(MAP)
for a in ac.get_all_level_actors():
 if not isinstance(a,(u.WorldSettings,u.LevelScriptActor)):ac.destroy_actor(a)
world.get_world_settings().set_editor_property('default_game_mode',u.load_class(None,'/Script/AshWell.AshWellIntroGameMode'))
V=lambda p:u.Vector(*p)
def mat(name,color,rough=.8,texture=None,worldscale=180,metal=0):
 m=ed.load_asset(B+'/'+name) or at.create_asset(name,B,u.Material,u.MaterialFactoryNew());ml.delete_all_material_expressions(m)
 def const(value,prop):
  n=ml.create_material_expression(m,u.MaterialExpressionConstant);n.r=value;ml.connect_material_property(n,'',prop)
 c=ml.create_material_expression(m,u.MaterialExpressionConstant3Vector);c.constant=u.LinearColor(*color,1)
 if texture:
  wp=ml.create_material_expression(m,u.MaterialExpressionWorldPosition);mask=ml.create_material_expression(m,u.MaterialExpressionComponentMask);mask.set_editor_property('r',True);mask.set_editor_property('g',True);mask.set_editor_property('b',False);mask.set_editor_property('a',False);ml.connect_material_expressions(wp,'',mask,ml.get_material_expression_input_names(mask)[0])
  scale=ml.create_material_expression(m,u.MaterialExpressionMultiply);scale.set_editor_property('const_b',1/worldscale);ml.connect_material_expressions(mask,'',scale,'A')
  t=ml.create_material_expression(m,u.MaterialExpressionTextureSample);t.texture=ed.load_asset(texture);assert t.texture;ml.connect_material_expressions(scale,'',t,'UVs')
  mul=ml.create_material_expression(m,u.MaterialExpressionMultiply);ml.connect_material_expressions(t,'RGB',mul,'A');ml.connect_material_expressions(c,'',mul,'B');ml.connect_material_property(mul,'',u.MaterialProperty.MP_BASE_COLOR)
 else:ml.connect_material_property(c,'',u.MaterialProperty.MP_BASE_COLOR)
 const(rough,u.MaterialProperty.MP_ROUGHNESS);const(metal,u.MaterialProperty.MP_METALLIC);const(.25,u.MaterialProperty.MP_SPECULAR);ml.recompile_material(m);ed.save_loaded_asset(m);return m
stone=mat('M_CourtyardLimestone',(.66,.62,.52),.87,'/Game/AshWell/Textures/V2/T_concrete_floor_worn_001_base_color',250)
earth=mat('M_CourtyardEarth',(.39,.36,.29),.94,'/Game/AshWell/Textures/V2/T_concrete_floor_worn_001_base_color',220)
path=mat('M_CourtyardRoad',(.64,.61,.54),.87,'/Game/AshWell/Textures/V2/T_concrete_floor_worn_001_base_color',220)
grass=mat('M_CourtyardMoss',(.055,.075,.035),.97,'/Game/AshWell/Textures/V2/T_rock_face_01_base_color',200)
bronze=mat('M_CourtyardBronze',(.13,.095,.044),.55,metal=.65)
leaf=mat('M_CourtyardFoliage',(.024,.042,.024),1);bark=mat('M_CourtyardBark',(.046,.034,.022),.96)
cube=ed.load_asset('/Engine/BasicShapes/Cube');cyl=ed.load_asset('/Engine/BasicShapes/Cylinder');sphere=ed.load_asset('/Engine/BasicShapes/Sphere');cone=ed.load_asset('/Engine/BasicShapes/Cone')
count=0
def actor(cls,name,p,rot=None):
 global count
 count+=1;a=ac.spawn_actor_from_class(cls,V(p),rot or u.Rotator());a.set_actor_label('AWM_'+name);a.set_folder_path('MountedExperiment');return a
def mesh(name,m,p,size,material,rot=None,solid=False):
 a=actor(u.StaticMeshActor,name,p,rot);c=a.static_mesh_component;c.set_static_mesh(m);a.set_actor_scale3d(V(tuple(v/100 for v in size)));c.set_material(0,material);c.set_collision_profile_name('BlockAll' if solid else 'NoCollision');return a
def box(n,p,size,material=stone,rot=None,solid=False):return mesh(n,cube,p,size,material,rot,solid)
# Outside ground closes the horizon; it is scenery and never expands the playable area.
box('DistantGround',(0,0,-120),(120000,120000,100),grass)
# One uninterrupted floor: collision never depends on decorative paving seams.
box('ContinuousFightFloor',(0,0,-35),(5700,4400,70),earth,solid=True)
box('WestSafeApron',(-2800,0,-35),(650,1300,70),path,solid=True)
# Broad worn crossing, with flat threshold markers for the retreat direction.
box('OldProcessionalRoad',(0,0,1),(5650,680,2),path)
for side in (-1,1):
 for i in range(15):box('RoadEdging',(-2540+i*365,side*365,4),(330,22,8),stone)
# Low periphery is readable to player, high outer collisions prevent leaving the slice.
for side in (-1,1):
 box('NorthSouthRetainingWall',(0,side*2120,65),(5660,100,130),stone,solid=True)
 box('EastWall',(2780,side*1030,100),(100,2100,200),stone,solid=True)
 box('WestWall',(-2780,side*1470,100),(100,1320,200),stone,solid=True)
 for i in range(9):
  x=-2620+i*650
  box('WallPillar',(x,side*2110,150),(160,160,300),stone,solid=True)
  box('WallPillarCap',(x,side*2110,312),(190,190,28),stone)
# West entrance: the safe edge can be recognized from the entire arena.
for y in (-560,560):
 box('GateFoot',(-2230,y,55),(240,240,110),stone)
 mesh('GateColumn',cyl,(-2230,y,360),(132,132,580),stone)
 box('GateCapital',(-2230,y,660),(200,200,90),stone)
box('GateLintel',(-2230,0,755),(240,1330,120),stone)
box('GateCornice',(-2230,0,840),(280,1450,60),stone)
for x in (-1880,-1800):box('RetreatThreshold',(x,0,2),(30,1100,4),bronze)
# Few coherent groups beyond combat bounds; keep the floor free of clutter.
boulder=ed.load_asset('/Game/AshWell/Meshes/ScansV2/SM_Scan_Boulder01_LOD0')
for i in range(14):
 a=i*2.39996;x=math.cos(a)*(4100+(i%3)*800);y=math.sin(a)*(3400+(i%4)*550)
 if x<-2300 and abs(y)<900:continue
 if boulder:
  p=actor(u.StaticMeshActor,'DistantRock', (x,y,-110));p.static_mesh_component.set_static_mesh(boulder);p.set_actor_scale3d(V((3+i%3,3+i%3,3+(i%4))));p.static_mesh_component.set_collision_profile_name('NoCollision');p.set_actor_rotation(u.Rotator(yaw=i*41),False)
for x,y in [(2050,2450),(500,2530),(-1300,2510),(1800,-2520),(-1200,-2500),(3400,1100),(3450,-1300)]:
 mesh('CypressTrunk',cyl,(x,y,200),(38,38,400),bark)
 for j in range(3):mesh('CypressCrown',sphere,(x,y,390+j*155),(270-j*60,240-j*50,460-j*60),leaf)
# A restrained roofless colonnade outside the east wall.
for y in range(-2200,2201,550):
 mesh('FarColumn',cyl,(3350,y,370),(180,180,740),stone)
 box('FarCapital',(3350,y,760),(230,230,80),stone)
box('FarEntablature',(3350,0,850),(260,4900,130),stone)
for side in (-1,1):
 for i in range(4):
  mesh('OuterMossBed',sphere,(-1700+i*1060,side*2025,1),(710,160,6),grass)
start=actor(u.PlayerStart,'PlayerStart',(-2050,0,100))
sun=actor(u.DirectionalLight,'LateAfternoonSun',(0,0,1600),u.Rotator(pitch=-27,yaw=-42));sun.light_component.set_mobility(u.ComponentMobility.MOVABLE);sun.light_component.set_intensity(3.8);sun.light_component.set_light_color(u.LinearColor(1,.78,.53,1));sun.light_component.set_editor_property('atmosphere_sun_light',True)
actor(u.SkyAtmosphere,'Atmosphere',(0,0,-100))
sky=actor(u.SkyLight,'SkyFill',(0,0,1100));sky.light_component.set_mobility(u.ComponentMobility.MOVABLE);sky.light_component.set_intensity(.62);sky.light_component.set_editor_property('real_time_capture',True)
fog=actor(u.ExponentialHeightFog,'DistanceHaze',(0,0,-450));fog.component.set_editor_property('fog_density',.006);fog.component.set_editor_property('fog_height_falloff',.16);fog.component.set_editor_property('start_distance',2500)
post=actor(u.PostProcessVolume,'FixedExposure',(0,0,0));post.set_editor_property('unbound',True);settings=post.get_editor_property('settings')
for key,value in [('override_auto_exposure_method',True),('auto_exposure_method',u.AutoExposureMethod.AEM_MANUAL),('override_auto_exposure_bias',True),('auto_exposure_bias',0.0),('override_auto_exposure_apply_physical_camera_exposure',True),('auto_exposure_apply_physical_camera_exposure',False),('override_bloom_intensity',True),('bloom_intensity',.12),('override_vignette_intensity',True),('vignette_intensity',.2),('override_motion_blur_amount',True),('motion_blur_amount',0.0)]:settings.set_editor_property(key,value)
post.set_editor_property('settings',settings)
assert le.save_current_level()
O=R/'Saved/MountedBoss';O.mkdir(parents=True,exist_ok=True);(O/'arena-build.json').write_text(json.dumps({'map':MAP,'actors':count,'clear_fight_size_cm':[4800,3800],'continuous_collision_floor':True,'baseline_map_edited':False},indent=2))
u.log('MOUNTED_ARENA_BUILT')
