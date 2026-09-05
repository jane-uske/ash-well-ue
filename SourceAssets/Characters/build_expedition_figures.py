"""Original procedural static expedition figures for the Ash Well UE look test.

Run: Blender --background --python build_expedition_figures.py
Dimensions use metres. X is forward, Y is right, Z is up. No external assets.
These are posed, unrigged set-dressing figures, not final animation characters.
"""
from pathlib import Path
import bpy
import math
import json
import random
from mathutils import Vector, Matrix

OUT = Path(__file__).resolve().parent
random.seed(1919)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
bpy.context.scene.unit_settings.system = 'METRIC'
bpy.context.scene.unit_settings.scale_length = 1.0
MATERIALS = {}
PARTS = []


def material(name, color, roughness, metallic=0.0, emission=0.0):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    bs = next(n for n in mat.node_tree.nodes if n.bl_idname == 'ShaderNodeBsdfPrincipled')
    bs.inputs['Base Color'].default_value = (*color, 1)
    bs.inputs['Roughness'].default_value = roughness
    bs.inputs['Metallic'].default_value = metallic
    if emission:
        bs.inputs['Emission Color'].default_value = (*color, 1)
        bs.inputs['Emission Strength'].default_value = emission
    MATERIALS[name] = mat


material('Cloth', (0.035, 0.047, 0.049), .88)
material('DarkSteel', (.095, .111, .112), .50, .83)
material('Rust', (.16, .083, .039), .80, .40)
material('Amber', (1.0, .36, .065), .25, .0, 4.0)
material('Leather', (.039, .029, .020), .73)


def finish(obj, mat):
    obj.data.materials.append(MATERIALS[mat])
    if obj.type == 'MESH':
        for poly in obj.data.polygons:
            poly.use_smooth = True
    PARTS.append(obj)
    return obj


def mesh(name, verts, faces, mat, uv=None):
    data = bpy.data.meshes.new(name)
    data.from_pydata(verts, [], faces)
    data.update()
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    if uv:
        layer = data.uv_layers.new(name='UVMap')
        for polygon in data.polygons:
            for li, vi in zip(polygon.loop_indices, polygon.vertices):
                layer.data[li].uv = uv[vi]
    return finish(obj, mat)


def ellipsoid(name, pos, dims, mat, segments=32, rings=20):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings, location=pos)
    obj = bpy.context.object
    obj.name = name
    obj.scale = dims
    return finish(obj, mat)


def tube(name, points, radius, mat, cyclic=False, sides=10):
    curve = bpy.data.curves.new(name, 'CURVE')
    curve.dimensions = '3D'
    curve.resolution_u = 1 if cyclic else 4
    curve.bevel_depth = radius
    curve.bevel_resolution = 1
    spline = curve.splines.new('BEZIER')
    spline.bezier_points.add(len(points)-1)
    for p, co in zip(spline.bezier_points, points):
        p.co = co
        p.handle_left_type = 'AUTO'
        p.handle_right_type = 'AUTO'
    spline.use_cyclic_u = cyclic
    obj = bpy.data.objects.new(name, curve)
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.convert(target='MESH')
    obj.select_set(False)
    return finish(obj, mat)


def ring(name, center, rx, ry, mat, radius=.004, count=48):
    x,y,z = center
    return tube(name, [(x+rx*math.cos(a*2*math.pi/count),y+ry*math.sin(a*2*math.pi/count),z) for a in range(count)],radius,mat,True)


def loft_z(name, rings, mat, count=48, wrinkles=.0, phase=0, caps=True):
    """Continuous garment/boot volume; ring = (z, center_x, center_y, rx, ry)."""
    verts=[]; uv=[]; faces=[]
    for j,(z,x,y,rx,ry) in enumerate(rings):
        t=j/max(1,len(rings)-1)
        for i in range(count):
            a=2*math.pi*i/count
            # Low-frequency drape and shallow diagonal compressed-cloth wrinkles.
            drape=math.sin(9*a+phase)*.45 + math.sin(17*a+z*48+phase)*.18
            crease=math.sin(z*94 + 4*math.sin(a*3)+phase)*.37
            d=wrinkles*(drape+crease)
            verts.append((x+(rx+d)*math.cos(a), y+(ry+d)*math.sin(a), z))
            uv.append((i/count,t))
        if j:
            for i in range(count):
                a=(j-1)*count+i; b=(j-1)*count+(i+1)%count
                faces.append((a,b,b+count,a+count))
    if caps:
        faces.append(tuple(reversed(range(count))))
        faces.append(tuple(range((len(rings)-1)*count,len(rings)*count)))
    return mesh(name,verts,faces,mat,uv)


def smooth_path(keys, steps=6):
    output=[]
    for idx in range(len(keys)-1):
        p0=Vector(keys[max(0,idx-1)][:3]); p1=Vector(keys[idx][:3])
        p2=Vector(keys[idx+1][:3]); p3=Vector(keys[min(len(keys)-1,idx+2)][:3])
        for j in range(steps):
            t=j/steps
            pos=.5*((2*p1)+(-p0+p2)*t+(2*p0-5*p1+4*p2-p3)*t*t+(-p0+3*p1-3*p2+p3)*t*t*t)
            radius=keys[idx][3]*(1-t)+keys[idx+1][3]*t
            output.append((pos,radius))
    output.append((Vector(keys[-1][:3]),keys[-1][3]))
    return output


def limb(name, keys, mat='Cloth', wrinkles=.004, oval=.92):
    path=smooth_path(keys)
    verts=[]; faces=[]; uv=[]; n=40
    for j,(p,r) in enumerate(path):
        direction=(path[min(j+1,len(path)-1)][0]-path[max(j-1,0)][0]).normalized()
        helper=Vector((1,0,0)) if abs(direction.x)<.85 else Vector((0,0,1))
        u=direction.cross(helper).normalized(); v=direction.cross(u).normalized()
        for i in range(n):
            a=i*2*math.pi/n
            fold=wrinkles*(math.sin(j*2.1+3*math.cos(a))+.35*math.sin(a*11+j*.45))
            q=p+u*((r+fold)*math.cos(a))+v*((r*oval+fold)*math.sin(a))
            verts.append(tuple(q)); uv.append((i/n,j/(len(path)-1)))
        if j:
            for i in range(n):
                a=(j-1)*n+i; b=(j-1)*n+(i+1)%n
                faces.append((a,b,b+n,a+n))
    faces.append(tuple(reversed(range(n))))
    faces.append(tuple(range((len(path)-1)*n,len(path)*n)))
    return mesh(name,verts,faces,mat,uv)


def cylinder(name, a, b, r, mat, vertices=28):
    a=Vector(a);b=Vector(b)
    obj=ellipsoid(name,(a+b)/2,(r,r,(b-a).length/2),mat,vertices,16)
    obj.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler()
    return obj


def shoulder_plate(y):
    # Curved overlapping cap around the deltoid; open underside.
    verts=[]; faces=[]
    for j in range(10):
        polar=.16+j/9*1.70
        for i in range(32):
            a=2*math.pi*i/32
            verts.append((.004+.117*math.sin(polar)*math.cos(a),y+.126*math.sin(polar)*math.sin(a),1.405+.095*math.cos(polar)))
        if j:
            for i in range(32):
                p=(j-1)*32+i;q=(j-1)*32+(i+1)%32
                faces.append((p,q,q+32,p+32))
    obj=mesh('Curved shoulder steel',verts,faces,'DarkSteel')
    sol=obj.modifiers.new('Forged plate thickness','SOLIDIFY');sol.thickness=.006
    tube('Shoulder rolled edge',verts[-32:],.005,'Rust',True)
    for xoff in [-.070,0,.070]:
        ellipsoid('Shoulder rivet',(xoff,y,1.505),(.008,.008,.004),'Rust',12,8)


def boot(x,y):
    profile=[(.014,x+.03,y,.142,.064),(.038,x+.032,y,.143,.068),(.060,x+.035,y,.140,.070),(.088,x+.036,y,.131,.069),(.119,x+.025,y,.112,.066),(.155,x+.006,y,.080,.062),(.18,x,y,.067,.058),(.225,x-.005,y,.063,.061),(.28,x-.006,y,.068,.064)]
    loft_z('Shaped reinforced leather boot',profile,'Leather',wrinkles=.0028)
    loft_z('Boot sole',[(.001,x+.03,y,.141,.066),(.015,x+.03,y,.145,.071),(.028,x+.03,y,.145,.071)],'DarkSteel',wrinkles=.001)
    for z in [.183,.225,.272]:
        ring('Boot strap',(x-.005,y,z),.069,.067,'Leather',.006)
    # Toe reinforcement follows the front of the shaped upper.
    ellipsoid('Toe cap',(x+.111,y,.075),(.065,.063,.036),'DarkSteel',24,12)
    for z in [.15,.178,.205]:
        tube('Boot fastening',[(x+.066,y-.034,z),(x+.078,y,z+.009),(x+.066,y+.034,z)],.004,'Rust')


def glove(wrist, raised=False):
    p=Vector(wrist)
    if raised:
        palm=p+Vector((.005,0,.067))
        ellipsoid('Raised open gloved palm',palm,(.022,.050,.071),'Leather')
        for i,dy in enumerate([-.034,-.012,.012,.034]):
            top=palm+Vector((.003,dy,.079-abs(dy)*.25))
            cylinder('Raised glove finger',palm+Vector((0,dy,.034)),top,.010,'Leather',16)
            ellipsoid('Finger tip',top,(.010,.010,.012),'Leather',16,10)
        cylinder('Glove thumb',palm+Vector((0,-.04,-.02)),palm+Vector((.008,-.072,.034)),.014,'Leather',16)
    else:
        palm=p+Vector((.011,0,-.049))
        ellipsoid('Closed gloved palm',palm,(.035,.043,.059),'Leather')
        for dy in [-.027,-.009,.009,.027]:
            cylinder('Curled glove finger',palm+Vector((.024,dy,-.029)),palm+Vector((.037,dy,.005)),.0095,'Leather',16)
        cylinder('Glove thumb',palm+Vector((.020,-.042,.016)),palm+Vector((.043,-.018,-.015)),.012,'Leather',16)
    ellipsoid('Glove dorsal protection',palm+Vector((-.022,0,.008)),(.013,.036,.038),'DarkSteel',24,14)


def lamp(wrist):
    p=Vector(wrist)+Vector((.018,0,-.070))
    center=p+Vector((0,0,-.192))
    x,y,z=center
    tube('Lantern bail',[(x,y-.052,z+.092),(x,y-.048,z+.174),(p.x,p.y,p.z),(x,y+.048,z+.174),(x,y+.052,z+.092)],.006,'DarkSteel')
    loft_z('Lantern glowing glass',[(z-.071,x,y,.040,.040),(z+.066,x,y,.040,.040)],'Amber',count=24)
    loft_z('Lantern base',[(z-.10,x,y,.050,.050),(z-.081,x,y,.057,.057),(z-.068,x,y,.046,.046)],'DarkSteel',count=32)
    loft_z('Lantern cap',[(z+.068,x,y,.047,.047),(z+.085,x,y,.058,.058),(z+.105,x,y,.030,.030)],'DarkSteel',count=32)
    for a in range(6):
        rad=a*2*math.pi/6
        dx=.050*math.cos(rad);dy=.050*math.sin(rad)
        tube('Lantern guard',[(x+dx,y+dy,z-.08),(x+dx,y+dy,z+.08)],.0035,'Rust')
    for zz in [z-.035,z+.035]:
        ring('Lantern wire ring',(x,y,zz),.052,.052,'DarkSteel',.0025,32)
    return list(center)


def build_figure(name, origin, yaw, stop=False):
    global PARTS
    PARTS=[]
    # Lower legs are visible beneath a heavy, long coat.
    for side in [-1,1]:
        y=side*.110
        x=.045 if side==1 else -.035
        boot(x,y)
        keys=[(x,y,.20,.057),(x-.012,y,.31,.062),(x-.004,y,.41,.080),(.012,y,.49,.084),(.006,y,.57,.079),(-.004,y,.69,.097),(-.005,y,.84,.112)]
        limb('Trouser leg with compressed knee folds',keys,wrinkles=.007,oval=.83)
        ellipsoid('Knee leather reinforcement',(.080+x*.3,y,.482),(.025,.070,.074),'Leather',28,16)
        ring('Lower trouser cuff',(x,y,.29),.064,.065,'Cloth',.006)
    # Full connected body and long tail, with high-count rings for cloth curvature.
    levels=[(.44,.117,.238),(.50,.122,.236),(.60,.130,.230),(.70,.139,.218),(.80,.145,.204),(.90,.143,.190),(1.00,.131,.175),(1.10,.141,.177),(1.20,.157,.195),(1.30,.172,.219),(1.38,.156,.244),(1.43,.136,.239),(1.47,.112,.189),(1.50,.083,.102)]
    dense=[]
    for i in range(len(levels)-1):
        a=levels[i];b=levels[i+1]
        for k in range(4):
            t=k/4
            dense.append((a[0]*(1-t)+b[0]*t,0,0,a[1]*(1-t)+b[1]*t,a[2]*(1-t)+b[2]*t))
    z,rx,ry=levels[-1];dense.append((z,0,0,rx,ry))
    loft_z('Continuous heavy expedition coat',dense,'Cloth',64,.0045)
    # Hem, back panel seams and fastening edge catch low grazing light.
    ring('Coat weighted hem',(0,0,.45),.121,.24,'Leather',.006)
    for yy in [-.112,.112]:
        tube('Long stitched coat back seam',[(-.124,yy,.47),(-.140,yy,.75),(-.142,yy,.93),(-.157,yy,1.19),(-.148,yy,1.36)],.0023,'Leather')
    for sy in [-1,1]:
        tube('Coat vertical flap',[(.108,sy*.110,.47),(.141,sy*.078,.70),(.145,sy*.056,.9),(.147,sy*.034,1.10),(.162,sy*.032,1.29),(.120,sy*.035,1.45)],.004,'Leather')
        # Soft hanging utility pouch, integrated rounded shape.
        ellipsoid('Belt supply pouch',(-.034,sy*.204,.935),(.078,.048,.107),'Leather',32,20)
        tube('Pouch flap seam',[(-.10,sy*.245,.971),(-.032,sy*.252,.952),(.029,sy*.245,.971)],.004,'Rust')
    loft_z('Heavy waist belt',[(.997,0,0,.144,.193),(1.026,0,0,.143,.192),(1.047,0,0,.143,.191)],'Leather',64)
    for yy in [-.151,.151]:
        tube('Harness shoulder strap',[(-.157,yy,1.03),(-.182,yy,1.24),(-.13,yy,1.43),(.005,yy,1.471),(.145,yy,1.30),(.139,yy,1.08)],.014,'Leather')
    # Raised scarf/hood collar; rear folds visibly merge into the shoulders.
    loft_z('Gathered high collar',[(1.46,-.016,0,.108,.116),(1.49,-.023,0,.120,.112),(1.53,-.027,0,.110,.100),(1.56,-.026,0,.098,.091)],'Cloth',48,.006)
    ellipsoid('Hood resting on upper back',(-.104,0,1.45),(.068,.128,.068),'Cloth',40,22)
    # Head is helmeted and masked; the rear view does not rely on a face texture.
    ellipsoid('Hooded head',(0,0,1.652),(.096,.083,.111),'Cloth',40,28)
    ellipsoid('Rounded steel helmet',(-.008,0,1.690),(.103,.093,.090),'DarkSteel',40,24)
    ring('Helmet lower rim',(-.006,0,1.668),.105,.095,'Leather',.005)
    tube('Helmet central spine',[(-.101,0,1.691),(-.061,0,1.755),(0,0,1.782),(.075,0,1.740),(.093,0,1.688)],.004,'Rust')
    ellipsoid('Dark respirator face',(.085,0,1.623),(.047,.066,.055),'DarkSteel',28,18)
    for sy in [-1,1]:
        ellipsoid('Eye visor',(.091,sy*.037,1.677),(.020,.031,.019),'DarkSteel',24,16)
        ellipsoid('Respirator side filter',(.083,sy*.058,1.604),(.032,.023,.026),'Rust',24,14)
        tube('Helmet side strap',[(.06,sy*.071,1.68),(.035,sy*.083,1.61),(-.020,sy*.076,1.586)],.008,'Leather')
    # Bent sleeves with curved shoulder/elbow, detailed cuff and gloves.
    wrists={}
    for sy in [-1,1]:
        if stop and sy==1:
            keys=[(-.004,.219,1.417,.083),(.015,.290,1.37,.081),(.063,.371,1.326,.071),(.102,.423,1.371,.067),(.117,.470,1.468,.054),(.109,.491,1.537,.049)]
        else:
            keys=[(0,sy*.224,1.418,.085),(.002,sy*.270,1.337,.085),(-.031,sy*.298,1.205,.073),(-.018,sy*.316,1.106,.069),(.023,sy*.339,1.015,.059),(.047,sy*.349,.937,.051)]
        limb('Tailored bent coat sleeve',keys,wrinkles=.0045)
        wrist=keys[-1][:3];wrists[sy]=wrist
        prev=Vector(keys[-2][:3]);end=Vector(wrist)
        limb('Heavy cuff gauntlet',[(*prev,.060),(*(prev.lerp(end,.7)),.059),(*end,.055)],'Leather',.002)
        glove(wrist,stop and sy==1)
        shoulder_plate(sy*.227)
        elbow=keys[3][:3]
        ellipsoid('Stitched elbow patch',Vector(elbow)+Vector((-.052,0,0)),(.020,.064,.072),'Leather',24,16)
    # Oxygen backpack: packed soft bag, two rounded metal cylinders, valves, straps.
    ellipsoid('Soft backpack',(-.217,0,1.214),(.090,.155,.218),'Leather',40,28)
    for sy in [-1,1]:
        cy=sy*.098
        loft_z('Oxygen canister',[(1.005,-.291,cy,.032,.032),(1.027,-.291,cy,.047,.047),(1.072,-.291,cy,.050,.050),(1.345,-.291,cy,.050,.050),(1.395,-.291,cy,.045,.045),(1.415,-.291,cy,.025,.025)],'DarkSteel',40)
        for zz in [1.085,1.308]:
            ring('Canister fastening band',(-.291,cy,zz),.055,.055,'Leather',.012)
        loft_z('Canister top valve',[(1.414,-.291,cy,.015,.015),(1.447,-.291,cy,.014,.014)],'Rust',24)
        ring('Canister valve wheel',(-.291,cy,1.448),.026,.026,'Rust',.004,24)
        tube('Ribbed breathing hose',[(-.291,cy,1.44),(-.258,sy*.176,1.489),(-.142,sy*.178,1.506),(.003,sy*.122,1.509),(.084,sy*.066,1.603)],.013,'Leather')
        for k in range(12):
            zz=1.100+k*.017
            ring('Tank wear ring',(-.291,cy,zz),.0506,.0506,'Rust',.0016,24)
    tube('Backpack lower U hose',[(-.270,-.097,1.029),(-.301,-.09,.963),(-.289,0,.943),(-.300,.089,.966),(-.273,.098,1.029)],.013,'DarkSteel')
    tube('Pack carry handle',[(-.202,-.063,1.391),(-.224,-.057,1.469),(-.220,.057,1.469),(-.202,.063,1.391)],.011,'Leather')
    light_local=lamp(wrists[-1] if stop else wrists[1])
    # Join and bake the world placement into geometry, preserving origin = world zero.
    bpy.ops.object.select_all(action='DESELECT')
    for obj in PARTS:
        obj.select_set(True)
        bpy.context.view_layer.objects.active=obj
        if obj.modifiers:
            for mod in list(obj.modifiers):
                bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.context.view_layer.objects.active=PARTS[0]
    bpy.ops.object.join()
    obj=bpy.context.object;obj.name=name
    bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
    # Consolidate slots explicitly so import order is deterministic.
    old=[m.name for m in obj.data.materials]
    ids=[list(MATERIALS).index(old[p.material_index]) for p in obj.data.polygons]
    obj.data.materials.clear()
    for mat in MATERIALS.values():obj.data.materials.append(mat)
    for p,i in zip(obj.data.polygons,ids):p.material_index=i
    rotation=Matrix.Rotation(math.radians(yaw),4,'Z')
    offset=Vector(origin)
    for v in obj.data.vertices:v.co=rotation@v.co+offset
    # Original UVs are retained; add a simple named layer for later UE lightmap generation.
    for p in obj.data.polygons:p.use_smooth=True
    obj.data.update()
    bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
    obj['asset_role']='static posed expedition worker, original procedural mesh'
    obj['source_forward_axis']='X'
    obj['source_length_unit']='metre'
    obj['requires_material_binding']='Cloth,DarkSteel,Rust,Amber,Leather'
    bpy.ops.export_scene.fbx(filepath=str(OUT/(name+'.fbx')),use_selection=True,object_types={'MESH'},use_mesh_modifiers=True,mesh_smooth_type='FACE',use_triangles=True,add_leaf_bones=False,bake_anim=False,axis_forward='-Y',axis_up='Z',global_scale=1.0,apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',use_custom_props=True)
    triangulated=sum(max(0,len(p.vertices)-2) for p in obj.data.polygons)
    bounds=[[min(v.co[i] for v in obj.data.vertices) for i in range(3)],[max(v.co[i] for v in obj.data.vertices) for i in range(3)]]
    return {'name':name,'fbx':name+'.fbx','origin_m':[0,0,0],'placement_baked_m':origin,'yaw_baked_deg':yaw,'bounds_m':bounds,'triangles':triangulated,'vertices':len(obj.data.vertices),'lantern_center_m':list(rotation@Vector(light_local)+offset),'material_slots':list(MATERIALS),'pose':'right hand stop gesture, left hand lantern' if stop else 'standing, right hand lantern'}


entries=[build_figure('SM_Expedition_Protagonist',[0,-.6,0],0),build_figure('SM_Expedition_Companion',[7,-.4,0],-18,True)]
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'ExpeditionFigures.blend'))
manifest={'asset_version':1,'generator':'build_expedition_figures.py','blender_version':bpy.app.version_string,'authorship':'Original procedural geometry made for Ash Well; no downloaded assets','purpose':'Static posed figures for the first UE visual sample; not rigged or animation ready','source_coordinates':'Metres, +X forward, +Y right, +Z up; each object origin is world zero and placement is baked into vertices','fbx_export':{'axis_forward':'-Y','axis_up':'Z','global_scale':1.0,'apply_unit_scale':True,'apply_scale_options':'FBX_SCALE_UNITS','unit_settings_scale_length':1.0,'notes':'FBX carries metre units. UE scene-unit conversion should yield centimetres. Verify the imported height is about 178 cm, facing +X, before enabling any Force Front X Axis override. Both actors should be placed at world origin when preserving baked positions.'},'material_parameters':{n:{'base_color':list(m.diffuse_color[:3]),'role':'emissive glass, bind an Unreal emissive material and add a point light using lantern_center_m' if n=='Amber' else n} for n,m in MATERIALS.items()},'assets':entries,'total_triangles':sum(e['triangles'] for e in entries)}
(OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
print('ASH_WELL_CHARACTER_MANIFEST '+json.dumps(manifest,ensure_ascii=False))
