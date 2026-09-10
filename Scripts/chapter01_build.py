"""Assemble the approved five-zone chapter via the native UE MCP project tool.
Only the new Chapter01 map/assets are authored. The original combat map is retained.
"""
from pathlib import Path
import unreal as u,math,json,random
from editor_toolset.toolsets.blueprint import BlueprintTools as B
R=Path(__file__).resolve().parents[1];BASE='/Game/AshWell/Chapter01';MAP=BASE+'/L_Chapter01_Descent'
ed=u.EditorAssetLibrary;levels=u.get_editor_subsystem(u.LevelEditorSubsystem);actors=u.get_editor_subsystem(u.EditorActorSubsystem);assets=u.AssetToolsHelpers.get_asset_tools()
assert not levels.is_in_play_in_editor()
if not ed.does_asset_exist(MAP):assert levels.new_level_from_template(MAP,'/Game/AshWell/Maps/FirstDescentIntro')
elif levels.get_current_level().get_outermost().get_name()!=MAP:assert levels.load_level(MAP)
world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world();assert world.get_path_name().startswith(MAP)
for a in actors.get_all_level_actors():
 if isinstance(a,(u.WorldSettings,u.LevelScriptActor)):continue
 label=a.get_actor_label();c=a.get_component_by_class(u.StaticMeshComponent);mesh=c.static_mesh if c else None;p=mesh.get_path_name() if mesh else ''
 keep=('/ArchitectureV2/' in p and '/Foreground/' not in p) or 'Cavern' in p or isinstance(a,(u.DirectionalLight,u.SkyLight,u.ExponentialHeightFog,u.PostProcessVolume)) or (isinstance(a,(u.PointLight,u.RectLight)) and ('WarmRoom' in label or 'Pier' in label or 'Monument' in label or 'FarRim' in label))
 if label.startswith('AWC_') or not keep:actors.destroy_actor(a)
 else:
  a.set_folder_path('Chapter01/InheritedFar');a.set_actor_enable_collision(False)

V=lambda p:u.Vector(*p)
XYZ=lambda v:(v.x,v.y,v.z)
M={k:ed.load_asset(p) for k,p in {'steel':'/Game/AshWell/Materials/V2/M_OldSteel','rust':'/Game/AshWell/Materials/V2/M_Rust','stone':'/Game/AshWell/Materials/V2/M_Concrete','floor':'/Game/AshWell/Materials/V2/M_WetStone','dark':'/Game/AshWell/Materials/M_DarkSteel','amber':'/Game/AshWell/Materials/M_Amber','rock':'/Game/AshWell/Materials/M_Rock'}.items()}
cube=ed.load_asset('/Engine/BasicShapes/Cube');cyl=ed.load_asset('/Engine/BasicShapes/Cylinder');count=0;floor_rows=[];collision_rows=[]
mel=u.MaterialEditingLibrary
def simple_material(name,color,emission=0):
 m=ed.load_asset(BASE+'/'+name) or assets.create_asset(name,BASE,u.Material,u.MaterialFactoryNew());mel.delete_all_material_expressions(m)
 c=mel.create_material_expression(m,u.MaterialExpressionConstant3Vector);c.constant=u.LinearColor(*color,1);mel.connect_material_property(c,'',u.MaterialProperty.MP_BASE_COLOR)
 r=mel.create_material_expression(m,u.MaterialExpressionConstant);r.r=.75;mel.connect_material_property(r,'',u.MaterialProperty.MP_ROUGHNESS)
 if emission:
  e=mel.create_material_expression(m,u.MaterialExpressionConstant3Vector);e.constant=u.LinearColor(*(v*emission for v in color),1);mel.connect_material_property(e,'',u.MaterialProperty.MP_EMISSIVE_COLOR)
 mel.recompile_material(m);ed.save_loaded_asset(m);return m
window=simple_material('M_Window',(.32,.19,.072),1.6);dimwindow=simple_material('M_WindowDim',(.032,.029,.021),.1)
# World-space UVs keep the long floor slabs at a consistent 1.5 metre texture scale.
fm=ed.load_asset(BASE+'/M_ChapterFloor') or assets.create_asset('M_ChapterFloor',BASE,u.Material,u.MaterialFactoryNew());mel.delete_all_material_expressions(fm)
wp=mel.create_material_expression(fm,u.MaterialExpressionWorldPosition);mask=mel.create_material_expression(fm,u.MaterialExpressionComponentMask)
for k,v in [('r',True),('g',True),('b',False),('a',False)]:mask.set_editor_property(k,v)
assert mel.connect_material_expressions(wp,'',mask,mel.get_material_expression_input_names(mask)[0]);scale=mel.create_material_expression(fm,u.MaterialExpressionMultiply);scale.set_editor_property('const_b',1/150);mel.connect_material_expressions(mask,'',scale,'A')
for suffix,prop,sampler in [('base_color',u.MaterialProperty.MP_BASE_COLOR,u.MaterialSamplerType.SAMPLERTYPE_COLOR),('roughness',u.MaterialProperty.MP_ROUGHNESS,u.MaterialSamplerType.SAMPLERTYPE_MASKS),('normal',u.MaterialProperty.MP_NORMAL,u.MaterialSamplerType.SAMPLERTYPE_NORMAL)]:
 t=mel.create_material_expression(fm,u.MaterialExpressionTextureSample);t.texture=ed.load_asset('/Game/AshWell/Textures/V2/T_slate_floor_03_'+suffix);t.sampler_type=sampler;mel.connect_material_expressions(scale,'',t,'UVs');mel.connect_material_property(t,'RGB' if suffix!='roughness' else 'R',prop)
mel.recompile_material(fm);ed.save_loaded_asset(fm);M['floor']=fm
kit={n:ed.load_asset(BASE+'/Meshes/SM_C1_'+n) for n in ['WorkerFacade','ClothAwning','WaterPump','WaterCan','TunnelFrame','CatwalkDeck','RailPanel','DepartureFrame','DepartureGate','CagedLamp']};assert all(kit.values())
def spawn(cls,name,pos,rot=None,folder='Chapter01/Structure'):
 global count
 count+=1;a=actors.spawn_actor_from_class(cls,V(pos),rot or u.Rotator());a.set_actor_label('AWC_'+name+'_'+str(count));a.set_folder_path(folder);return a
def static(name,mesh,p,scale=(1,1,1),mat=None,rot=None,solid=False,folder='Chapter01/Structure'):
 a=spawn(u.StaticMeshActor,name,p,rot,folder);c=a.static_mesh_component;c.set_static_mesh(mesh);a.set_actor_scale3d(V(scale));c.set_collision_profile_name('BlockAll' if solid else 'NoCollision')
 if mat:c.set_material(0,M[mat] if isinstance(mat,str) else mat)
 return a
def box(name,p,size,mat='steel',solid=False,rot=None,folder='Chapter01/Structure'):
 a=static(name,cube,p,tuple(x/100 for x in size),mat,rot,solid,folder)
 if solid:collision_rows.append(name)
 return a
def part(name,p,yaw=0,scale=(1,1,1),folder='Chapter01/Details'):
 a=static(name,kit[name],p,scale,None,u.Rotator(pitch=0,yaw=yaw,roll=0),False,folder)
 if name=='WorkerFacade':
  for i,s in enumerate(kit[name].static_materials):
   if 'Amber' in str(s.material_slot_name):a.static_mesh_component.set_material(i,dimwindow if int(abs(p[0])/550)%3==0 else window)
 return a
def beam(name,a,b,r=4,mat='rust'):
 aa=V(a);bb=V(b);d=bb-aa;return static(name,cyl,XYZ((aa+bb)*.5),(r/50,r/50,d.length()/100),mat,u.MathLibrary.make_rot_from_z(d))
def lamp(p,intensity=700,radius=750):
 part('CagedLamp',p);a=spawn(u.PointLight,'Worklight',(p[0],p[1],p[2]-25),folder='Chapter01/Lighting');c=a.point_light_component;c.set_editor_property('intensity_units',u.LightUnits.LUMENS);c.set_intensity(intensity);c.set_attenuation_radius(radius);c.set_light_color(u.LinearColor(1,.46,.17,1));c.set_cast_shadows(False)
def fill(p,intensity=2000,radius=1400,color=(.30,.43,.52)):
 a=spawn(u.PointLight,'Bounce',p,folder='Chapter01/Lighting');c=a.point_light_component;c.set_editor_property('intensity_units',u.LightUnits.LUMENS);c.set_intensity(intensity);c.set_attenuation_radius(radius);c.set_light_color(u.LinearColor(*color,1));c.set_cast_shadows(False)
def floor(name,a,b,width,material='floor'):
 aa=V(a);bb=V(b);d=bb-aa;mid=(aa+bb)*.5;mid.z-=22
 q=box(name,XYZ(mid),(d.length()+12,width,44),material,True,u.MathLibrary.find_look_at_rotation(aa,bb),'Chapter01/Walkable')
 floor_rows.append({'name':name,'a':a,'b':b,'width':width});return q
def rail(a,b):
 aa=V(a);bb=V(b);d=bb-aa;mid=(aa+bb)*.5
 for height,r in [(12,4),(58,3),(112,4)]:beam('RailTube',XYZ(aa+V((0,0,height))),XYZ(bb+V((0,0,height))),r)
 n=max(1,math.ceil(d.length()/180))
 for i in range(n+1):
  p=aa+d*i/n;box('RailPost',XYZ(p+V((0,0,55))),(7,8,110),'steel')
 q=box('RailSafety',XYZ(mid+V((0,0,70))),(d.length(),12,140),'dark',True,u.MathLibrary.find_look_at_rotation(aa,bb),'Chapter01/Collision');q.set_actor_hidden_in_game(True)

# 01: a short, inhabited ration street. Its exit gate frames the way down.
floor('RationStreet',(-11500,800,1600),(-7420,800,1600),1540)
box('StreetBack',(-11530,800,1900),(70,1540,600),'stone',True)
for side in [-1,1]:
 y=800+side*800;yaw=180 if side==-1 else 0
 box('HousingRear',(-9400,y+side*100,2020),(4200,160,840),'stone',True)
 for i,x in enumerate(range(-11100,-7799,550)):
  part('WorkerFacade',(x,y,1600),yaw,folder='Chapter01/RationStreet')
  if i%2==0:part('ClothAwning',(x,y-side*65,1600),yaw,folder='Chapter01/RationStreet')
  lamp((x,y-side*190,1880),520,760)
  for j in range(2):part('WaterCan',(x+80+j*48,y-side*100,1600),i*34)
 box('StreetEave',(-9440,y,2490),(4400,240,100),'dark')
for x in [-11300,-10200,-9100,-8000]:
 for y in [20,1580]:box('StreetPier',(x,y,2190),(45,70,1200),'rust')
 beam('StreetCrossbrace',(x,0,2700),(x,1600,2700),17)
 fill((x,800,2120),2200,1450,(.42,.43,.40))
part('WaterPump',(-10100,280,1600),0,folder='Chapter01/RationStreet')
box('PumpCollision',(-10100,280,1700),(210,125,200),'dark',True).set_actor_hidden_in_game(True)
for i in range(5):part('WaterCan',(-10300-i*85,450+(i%2)*65,1600),i*27)
part('DepartureFrame',(-7500,800,1600),0)
gate=part('DepartureGate',(-7500,800,1600),0);gate.static_mesh_component.set_mobility(u.ComponentMobility.MOVABLE);gate.static_mesh_component.set_collision_profile_name('BlockAll')
for y in [160,1440]:box('GateWall',(-7500,y,1840),(100,630,480),'stone',True)

# Reuse the existing worker skeletal mesh for a few ordinary residents; no new character style.
resident=ed.load_asset('/Game/AshWell/Intro/Characters/SK_Intro_Companion');idle=ed.load_asset('/Game/AshWell/Intro/Characters/A_Intro_Companion_Idle')
for i,p in enumerate([(-10600,420,1600),(-10800,400,1600),(-10360,350,1600),(-8840,1330,1600)]):
 a=spawn(u.SkeletalMeshActor,'Resident',p,u.Rotator(pitch=0,yaw=30+i*27,roll=0),'Chapter01/Residents');c=a.skeletal_mesh_component;c.set_skeletal_mesh_asset(resident);c.set_collision_profile_name('NoCollision');a.set_actor_scale3d(V((1,-1,1)));c.set_animation_mode(u.AnimationMode.ANIMATION_SINGLE_NODE)
 data=c.get_editor_property('animation_data');data.set_editor_property('anim_to_play',idle);data.set_editor_property('saved_looping',True);c.set_editor_property('animation_data',data)

# 02: enclosed descent, wide enough for a third-person camera.
floor('TunnelDescent',(-7420,800,1600),(-3900,800,800),620,'floor')
for i,x in enumerate(range(-7380,-3899,300)):
 z=1600+(x+7420)/3520*-800
 part('TunnelFrame',(x,800,z),0,folder='Chapter01/Tunnel')
 for s in [-1,1]:
  box('TunnelWall',(x,800+s*360,z+230),(330,100,520),'rock',True,folder='Chapter01/Tunnel')
  beam('ServicePipe',(x-150,800+s*282,z+305),(x+150,800+s*282,z+237),10,'rust')
 box('TunnelRoof',(x,800,z+600),(350,830,140),'rock',False,folder='Chapter01/Tunnel')
 if i%2==0:lamp((x,1070,z+330),1000,1000)
 if i%3==0:fill((x,800,z+260),800,800,(.35,.37,.39))

# 03: continuous catwalk, clear right-angle landings and a gradual descent.
path=[(-3900,800,800),(-2600,800,800),(-2600,2000,800),(-2370,2000,800),(-730,2000,350),(-500,2000,350),(-500,800,350),(-270,800,350),(1470,800,0),(1700,800,0),(2390,800,0)]
width=360
for i,(a,b) in enumerate(zip(path,path[1:])):
 floor('CliffWalk_%02d'%i,a,b,width,'steel')
 aa=V(a);bb=V(b);d=bb-aa;n=max(1,math.ceil(d.length()/400));rot=u.MathLibrary.find_look_at_rotation(aa,bb)
 for j in range(n):
  p=aa+d*(j+.5)/n;p.z-=2
  static('DeckModule',kit['CatwalkDeck'],XYZ(p),(d.length()/n/400,width/280,1),None,rot)
 for j in range(max(1,math.ceil(d.length()/600))+1):
  f=j/max(1,math.ceil(d.length()/600));p=aa+d*f
  beam('Cantilever',(p.x,p.y-180,p.z-70),(p.x,p.y-700,p.z-600),18)
  if j%2==0:lamp((p.x,p.y+width/2-25,p.z+180),780,950)
for p in [(-2600,800,800),(-2600,2000,800),(-500,2000,350),(-500,800,350)]:box('CornerLanding',(p[0],p[1],p[2]-22),(width,width,44),'steel',True,folder='Chapter01/Walkable')
for side in [-1,1]:
 outline=[]
 for i,p in enumerate(path):
  dirs=[]
  for a,b in ([(path[i-1],p)] if i else [])+([(p,path[i+1])] if i<len(path)-1 else []):
   dx=b[0]-a[0];dy=b[1]-a[1];L=math.hypot(dx,dy);dirs.append((-dy/L,dx/L))
  nx=sum(d[0] for d in dirs);ny=sum(d[1] for d in dirs);L=math.hypot(nx,ny);nx/=L;ny/=L
  denom=nx*dirs[0][0]+ny*dirs[0][1];w=135 if i==len(path)-1 else width/2
  outline.append((p[0]+side*nx*w/denom,p[1]+side*ny*w/denom,p[2]))
 for a,b in zip(outline,outline[1:]):rail(a,b)

# Scanned rock is fitted by its real mesh bounds rather than arbitrary import units.
rock=ed.load_asset('/Game/AshWell/Meshes/ScansV2/SM_Scan_Boulder01_LOD0');rockmat=ed.load_asset('/Game/AshWell/Materials/V2/M_Scan_boulder_01')
def rockfit(p,size):
 b=rock.get_bounding_box();center=(b.min+b.max)*.5;extent=b.max-b.min;sc=V((size[0]/extent.x,size[1]/extent.y,size[2]/extent.z));loc=V(p)-V((center.x*sc.x,center.y*sc.y,center.z*sc.z))
 return static('CliffRock',rock,XYZ(loc),XYZ(sc),rockmat,solid=False,folder='Chapter01/Rock')
for x in range(-11700,-3500,900):
 rockfit((x,-400,1400),(1350,1200,3400));rockfit((x,2080,1800),(1300,1350,4400))
for x in [-3500,-2500,-1400,-300,900,1900]:rockfit((x,-750,-400),(1700,1250,3200))
for x in range(-11400,-7600,900):rockfit((x,800,3250),(1550,2300,1050))
# A visible load-bearing pier and crane emphasize the station without occupying its floor.
box('StationSupport',(4350,2200,-1900),(320,480,5800),'stone')
for z in range(-4500,1100,600):box('PierCollar',(4350,2200,z),(370,530,60),'rust')
beam('CraneMast',(4330,2230,900),(4330,2230,2000),24)
beam('CraneArm',(4330,2230,1830),(3150,1100,1830),18)
beam('CraneStay',(4330,2230,2000),(3150,1100,1830),5)
beam('HoistCable',(3150,1100,1830),(3150,1100,960),2,'steel')
for x in [-3400,-1600,400]:fill((x,1600,1650),4400,2300)

# Physical wayfinding signs use the already bundled OFL Chinese font.
plane=ed.load_asset('/Engine/BasicShapes/Plane')
for name,p,rot,w in [('water',(-10100,100,1950),u.Rotator(pitch=0,yaw=0,roll=-90),280),('departure',(-7570,800,2070),u.Rotator(pitch=0,yaw=-90,roll=90),420),('station',(2670,1060,190),u.Rotator(pitch=0,yaw=-90,roll=90),180)]:
 texpath=BASE+'/Signs/T_'+name
 if not ed.does_asset_exist(texpath):
  t=u.AssetImportTask();t.filename=str(R/'SourceAssets/Chapter01/Signs'/(name+'.png'));t.destination_path=BASE+'/Signs';t.destination_name='T_'+name;t.automated=True;t.save=True;assets.import_asset_tasks([t])
 m=ed.load_asset(BASE+'/Signs/M_'+name) or assets.create_asset('M_'+name,BASE+'/Signs',u.Material,u.MaterialFactoryNew());mel.delete_all_material_expressions(m);m.set_editor_property('two_sided',True)
 tex=mel.create_material_expression(m,u.MaterialExpressionTextureSample);tex.texture=ed.load_asset(texpath);mel.connect_material_property(tex,'RGB',u.MaterialProperty.MP_BASE_COLOR)
 em=mel.create_material_expression(m,u.MaterialExpressionMultiply);em.set_editor_property('const_b',.35);mel.connect_material_expressions(tex,'RGB',em,'A');mel.connect_material_property(em,'',u.MaterialProperty.MP_EMISSIVE_COLOR);mel.recompile_material(m);ed.save_loaded_asset(m)
 static('Sign_'+name,plane,p,(-w/100,w/400,1),m,rot,False,'Chapter01/Signs')

box('StationSignPost',(2670,980,95),(8,8,190),'rust')
beam('StationSignArm',(2670,980,190),(2670,1060,190),3,'rust')

# Explicit native chapter director and a map-local game mode preserve all combat values.
route=[(-11000,800,1690),(-10100,800,1690),(-7900,800,1690),(-7300,800,1663),(-5600,800,1276),(-3950,800,901),(-2750,800,890),(-2600,800,890),(-2600,2000,890),(-2370,2000,890),(-730,2000,440),(-500,2000,440),(-500,800,440),(-270,800,440),(1470,800,90),(1700,800,90),(2490,800,90),(2820,800,90)]
director=spawn(u.load_class(None,'/Script/AshWell.AshWellChapterDirector'),'Director',(0,0,0),folder='Chapter01/Gameplay');director.set_editor_property('route_points',[V(p) for p in route]);director.set_editor_property('pump_point',V((-10100,300,1600)));director.set_editor_property('departure_gate',gate)
gm=ed.load_asset(BASE+'/BP_Chapter01GameMode') or B.create(BASE,'BP_Chapter01GameMode',u.GameModeBase.static_class());B.compile_blueprint(gm);cdo=B.get_default_object(gm)
cdo.set_editor_property('default_pawn_class',u.load_class(None,'/Script/AshWell.AshWellCombatCharacter'));cdo.set_editor_property('player_controller_class',u.load_class(None,'/Script/AshWell.AshWellIntroPlayerController'));cdo.set_editor_property('hud_class',u.load_class(None,'/Script/AshWell.AshWellIntroHUD'));ed.save_loaded_asset(gm)
world.get_world_settings().set_editor_property('default_game_mode',gm.generated_class());spawn(u.PlayerStart,'Start',route[0],folder='Chapter01/Gameplay')
# Editor preview cameras are map actors, never exported as mesh assets.
for name,p,r in [('Ration',(-11280,830,1870),(-8,0,0)),('Tunnel',(-6700,800,1580),(-10,0,0)),('Overlook',(-3700,620,1030),(-8,8,0)),('Station',(2550,700,250),(-8,15,0))]:
 cam=spawn(u.CameraActor,'View_'+name,p,u.Rotator(pitch=r[0],yaw=r[1],roll=r[2]),'Chapter01/Cameras');cam.get_component_by_class(u.CameraComponent).set_field_of_view(73)
# Repair shared player weapon materials for Metal while retaining their geometry.
hammer_script=R/'Scripts/import_player_hammer.py'
exec(compile(hammer_script.read_text(),str(hammer_script),'exec'),{'__file__':str(hammer_script),'MATERIALS_ONLY':True})
assert levels.save_current_level();ed.save_directory(BASE,only_if_is_dirty=True,recursive=True)
u.get_editor_subsystem(u.UnrealEditorSubsystem).set_level_viewport_camera_info(V((-11300,850,1920)),u.Rotator(pitch=-10,yaw=0,roll=0))
report={'ok':True,'map':MAP,'new_actors':count,'walkable_floors':floor_rows,'route':route,'modules':list(kit),'native_combat_reused':True,'geometry_scope':'new Chapter01 map plus ten original Blender modules'}
(R/'Saved/Chapter01/build-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
