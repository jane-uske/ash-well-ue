"""V2 worn industrial expedition figures for the Ash Well UE look test.

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
material('DarkSteel', (.048, .055, .052), .74, .60)
material('Rust', (.16, .083, .039), .80, .40)
material('Amber', (1.0, .36, .065), .25, .0, 4.0)
material('Leather', (.039, .029, .020), .73)
material('Canvas', (.062, .058, .041), .94)


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


def ellipsoid(name, pos, dims, mat, segments=40, rings=28):
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


def loft_z(name, rings, mat, count=64, wrinkles=.0, phase=0, caps=True, boxiness=1.0):
    """Continuous garment/boot volume; ring = (z, center_x, center_y, rx, ry)."""
    verts=[]; uv=[]; faces=[]
    for j,(z,x,y,rx,ry) in enumerate(rings):
        t=j/max(1,len(rings)-1)
        for i in range(count):
            a=2*math.pi*i/count
            drape=math.sin(7*a+phase+z*3.2)*.65 + math.sin(13*a+z*18+phase)*.25
            crease=math.sin(z*76 + 2.7*math.sin(a*2)+phase)*.25
            d=wrinkles*(drape+crease)
            zz=z
            if 'expedition coat' in name:
                # Large hanging folds below the waist, diagonal tension at belt and back.
                skirt=max(0,min(1,(1.02-z)/.50))
                d+=skirt*(.010*math.sin(8*a+.8*z)+.004*math.sin(15*a+z*3))
                zz+=skirt*(.014*math.sin(3*a+.6)+.008*math.sin(7*a+1.2))
                back=max(0,-math.cos(a))**8
                d+=.012*math.exp(-((z-.94)/.15)**2)*math.sin(z*34+6*a)
                zz+=skirt*back*.012
            ca=math.copysign(abs(math.cos(a))**boxiness,math.cos(a))
            sa=math.copysign(abs(math.sin(a))**boxiness,math.sin(a))
            verts.append((x+(rx+d)*ca, y+(ry+d)*sa, zz))
            uv.append((i/count,t))
        if j:
            for i in range(count):
                a=(j-1)*count+i; b=(j-1)*count+(i+1)%count
                faces.append((a,b,b+count,a+count))
    if caps:
        faces.append(tuple(reversed(range(count))))
        faces.append(tuple(range((len(rings)-1)*count,len(rings)*count)))
    return mesh(name,verts,faces,mat,uv)


def smooth_path(keys, steps=14):
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
    verts=[]; faces=[]; uv=[]; n=64
    for j,(p,r) in enumerate(path):
        direction=(path[min(j+1,len(path)-1)][0]-path[max(j-1,0)][0]).normalized()
        helper=Vector((1,0,0)) if abs(direction.x)<.85 else Vector((0,0,1))
        u=direction.cross(helper).normalized(); v=direction.cross(u).normalized()
        for i in range(n):
            a=i*2*math.pi/n
            t=j/(len(path)-1)
            # Isolated, oblique folds on the compressed side of the limb. Avoid evenly
            # spaced circumferential waves: those read as an inflated suit or bellows.
            fold=wrinkles*.22*math.sin(a*3+t*8)
            fold+=wrinkles*.24*math.sin(t*14+2.3*a)*math.exp(-((t-.25)/.31)**2)
            for idx,center in enumerate([.43,.515,.59,.735,.875,.958]):
                tc=center+.028*math.sin(a*2+idx*.71)
                width=.022 if idx<4 else .014
                mask=.22+.78*max(0,math.cos(a-.43-idx*.27))**2
                ridge=math.exp(-((t-tc)/width)**2)-.43*math.exp(-((t-tc-width*1.18)/(width*.85))**2)
                fold+=wrinkles*(1.1 if idx<4 else .70)*mask*ridge
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
    # Small flat forged reinforcement set into a padded shoulder, not a round pauldron.
    verts=[]; faces=[]
    for j in range(10):
        polar=.18+j/9*1.52
        for i in range(32):
            a=2*math.pi*i/32
            verts.append((-.004+.090*math.sin(polar)*math.cos(a),y+.071*math.sin(polar)*math.sin(a),1.424+.037*math.cos(polar)+.002*math.sin(a*5)))
        if j:
            for i in range(32):
                p=(j-1)*32+i;q=(j-1)*32+(i+1)%32
                faces.append((p,q,q+32,p+32))
    obj=mesh('Curved shoulder steel',verts,faces,'DarkSteel')
    sol=obj.modifiers.new('Forged plate thickness','SOLIDIFY');sol.thickness=.003
    tube('Shoulder rolled edge',verts[-32:],.0028,'Rust',True)
    for xoff in [-.060,.060]:
        ellipsoid('Shoulder rivet',(xoff,y,1.45),(.0045,.0045,.003),'Rust',12,8)


def ribbon(name, points, width, mat='Canvas', side=(0,1,0), thickness=.0022):
    path=smooth_path([(*p,1) for p in points],6)
    vertices=[];faces=[];uv=[]
    across=Vector(side).normalized()
    length=0
    for j,(p,_) in enumerate(path):
        if j:length+=(p-path[j-1][0]).length
        for s in [-1,1]:
            vertices.append(tuple(p+across*width*s/2))
            uv.append(((s+1)*width/2,length))
        if j:faces.append((2*j-2,2*j-1,2*j+1,2*j))
    obj=mesh(name,vertices,faces,mat,uv)
    sol=obj.modifiers.new('Woven binding thickness','SOLIDIFY');sol.thickness=thickness
    return obj


def buckle(name, x, y, z, width=.035, height=.028):
    tube(name,[(x,y-width/2,z-height/2),(x,y+width/2,z-height/2),(x,y+width/2,z+height/2),(x,y-width/2,z+height/2)],.0024,'Rust',True)
    tube(name+' tongue',[(x-.001,y,z-height*.4),(x-.003,y,z+height*.35)],.0019,'DarkSteel')


def soft_box(name, center, halfdims, mat='Canvas', folds=.003):
    x,y,z=center;dx,dy,dz=halfdims
    rings=[]
    for j in range(37):
        t=-1+2*j/36
        edge=(1-abs(t)**8)**.25
        edge=.20+.80*edge
        rings.append((z+t*dz,x+.003*math.sin(t*4),y,dx*edge,dy*edge))
    return loft_z(name,rings,mat,72,folds,boxiness=.40)


def worn_pack():
    soft_box('Old rectangular canvas field pack',(-.222,-.013,1.213),(.077,.131,.180),'Canvas',.0048)
    # Overhanging folded top flap spans the bag, visibly separate from the soft body.
    vertices=[];faces=[];uv=[]
    for j in range(25):
        z=1.200+j/24*.196
        for k in range(37):
            y=-.155+k/36*.283
            x=-.310+.004*math.sin(y*48+z*21)+.011*((y+.013)/.143)**4
            if z>1.347:x+=.045*((z-1.347)/.049)**2
            zz=z+.004*math.sin(y*25)
            vertices.append((x,y,zz));uv.append((y+.155,z-1.2))
            if j and k:
                p=j*37+k;faces.append((p-38,p-37,p,p-1))
    flap=mesh('Canvas pack folded storm flap',vertices,faces,'Canvas',uv)
    sol=flap.modifiers.new('Heavy canvas flap edge','SOLIDIFY');sol.thickness=.003
    tube('Pack flap worn binding',[(-.309,-.149,1.225),(-.316,-.089,1.203),(-.315,-.012,1.207),(-.311,.067,1.198),(-.300,.126,1.219)],.0035,'Leather')
    for y in [-.091,.067]:
        ribbon('Pack longitudinal webbing',[(-.293,y,1.050),(-.315,y,1.149),(-.319,y,1.289),(-.282,y,1.393),(-.176,y,1.397)],.027,'Leather')
        buckle('Pack antique buckle',-.324,y,1.167)
        ribbon('Loose strap end',[(-.326,y,1.169),(-.329,y+.004,1.121),(-.324,y-.003,1.084)],.023,'Leather')
    soft_box('Back pocket',(-.312,-.013,1.087),(.023,.082,.057),'Canvas',.0028)
    tube('Pack pocket stitch',[(-.339,-.089,1.113),(-.342,-.007,1.103),(-.338,.062,1.111)],.0015,'Leather')
    ribbon('Pack carry loop',[(-.204,-.069,1.387),(-.224,-.057,1.423),(-.222,.022,1.422),(-.204,.046,1.390)],.015,'Canvas',side=(1,0,0))
    # One modest oxygen bottle held in a canvas sleeve on the right, with a worn valve.
    cy=.163
    loft_z('Small oxygen bottle',[(1.087,-.223,cy,.017,.017),(1.106,-.223,cy,.032,.032),(1.343,-.223,cy,.031,.031),(1.370,-.223,cy,.016,.016)],'DarkSteel',48)
    loft_z('Canvas bottle sleeve',[(1.098,-.223,cy,.034,.034),(1.164,-.223,cy,.035,.035),(1.254,-.223,cy,.035,.035),(1.306,-.223,cy,.034,.034)],'Canvas',64,.002)
    for z in [1.153,1.279]:
        ring('Bottle leather restraint',(-.223,cy,z),.038,.038,'Leather',.0065,40)
    loft_z('Bottle valve',[(1.368,-.223,cy,.012,.012),(1.397,-.223,cy,.012,.012)],'Rust',24)
    ring('Valve wheel',(-.223,cy,1.399),.021,.021,'Rust',.003,24)
    tube('Breathing tube',[(-.222,cy,1.397),(-.206,.208,1.419),(-.106,.193,1.448),(.008,.121,1.490),(.073,.060,1.584)],.009,'Leather')
    # A wrapped bedroll, a tool handle, and a loose repair cord add an irregular silhouette.
    roll=cylinder('Folded ground sheet',(-.229,-.129,1.011),(-.229,.097,1.011),.044,'Canvas',40)
    for yy in [-.084,.047]:
        ribbon('Bedroll tie',[(-.220,yy,1.057),(-.279,yy,1.031),(-.273,yy,.978),(-.204,yy,.974)],.015,'Leather')
    tube('Old hand tool shaft',[(-.218,-.180,1.054),(-.232,-.190,1.221)],.008,'DarkSteel')
    tube('Old hand tool head',[(-.232,-.190,1.221),(-.258,-.190,1.245),(-.249,-.190,1.265)],.009,'Rust')
    for k in range(3):
        tube('Looped repair cord',[(-.239-k*.005,-.139,1.331),(-.310-k*.002,-.148,1.240),(-.329-k*.002,-.140,1.152),(-.287-k*.002,-.122,1.132),(-.236,-.128,1.329)],.003,'Canvas')


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
        ellipsoid('Natural clenched gloved palm',palm,(.029,.039,.044),'Leather')
        for i,dy in enumerate([-.025,-.008,.009,.025]):
            tube('Curled gripping glove finger',[tuple(palm+Vector((.010,dy,.019))),tuple(palm+Vector((.035,dy,.012))),tuple(palm+Vector((.034,dy,-.021))),tuple(palm+Vector((.012,dy,-.025)))],.0105 if i in [1,2] else .009,'Leather')
            tube('Glove finger crease',[tuple(palm+Vector((.034,dy-.006,.003))),tuple(palm+Vector((.037,dy,.002))),tuple(palm+Vector((.033,dy+.006,.001)))],.0011,'Cloth')
        cylinder('Glove thumb',palm+Vector((.013,-.035,.021)),palm+Vector((.038,-.015,-.009)),.013,'Leather',24)
    ellipsoid('Glove soft dorsal patch',palm+Vector((-.023,0,.006)),(.008,.031,.032),'Canvas',32,20)
    for dy in [-.019,0,.019]:
        tube('Glove dorsal stitching',[tuple(palm+Vector((-.029,dy,-.016))),tuple(palm+Vector((-.033,dy,.008))),tuple(palm+Vector((-.025,dy,.026)))],.0012,'Leather')


def lamp(wrist):
    p=Vector(wrist)+Vector((.018,0,-.070))
    center=p+Vector((0,0,-.192))
    x,y,z=center
    tube('Lantern bail',[(x,y-.052,z+.092),(x,y-.048,z+.174),(p.x+.011,p.y-.028,p.z+.022),(p.x+.011,p.y+.028,p.z+.022),(x,y+.048,z+.174),(x,y+.052,z+.092)],.0045,'DarkSteel')
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
        y=side*.112
        x=.052 if side==1 else -.046
        boot(x,y)
        keys=[(x,y,.20,.057),(x-.012,y,.31,.062),(x-.004,y,.41,.080),(.012,y,.49,.084),(.006,y,.57,.079),(-.004,y,.69,.097),(-.005,y,.84,.112)]
        limb('Trouser leg with compressed knee folds',keys,wrinkles=.008,oval=.86)
        ellipsoid('Knee leather reinforcement',(.080+x*.3,y,.482),(.025,.070,.074),'Leather',28,16)
        ring('Lower trouser cuff',(x,y,.29),.064,.065,'Cloth',.006)
    # Full connected body and long tail, with high-count rings for cloth curvature.
    levels=[(.445,.119,.220),(.50,.125,.225),(.60,.135,.222),(.70,.143,.209),(.80,.148,.195),(.90,.145,.182),(1.00,.134,.174),(1.10,.145,.181),(1.20,.165,.201),(1.30,.169,.224),(1.38,.151,.240),(1.43,.125,.225),(1.47,.110,.184),(1.50,.089,.115)]
    dense=[]
    for i in range(len(levels)-1):
        a=levels[i];b=levels[i+1]
        for k in range(8):
            t=k/8
            dense.append((a[0]*(1-t)+b[0]*t,0,0,a[1]*(1-t)+b[1]*t,a[2]*(1-t)+b[2]*t))
    z,rx,ry=levels[-1];dense.append((z,0,0,rx,ry))
    coat=loft_z('Continuous heavy expedition coat',dense,'Cloth',112,.0075)
    # Hem, back panel seams and fastening edge catch low grazing light.
    hem=[]
    for i in range(112):
        a=i*2*math.pi/112
        d=.0075*(math.sin(7*a+.445*3.2)*.65+math.sin(13*a+.445*18)*.25+math.sin(.445*76+2.7*math.sin(a*2))*.25)
        d+=.010*math.sin(8*a+.8*.445)+.004*math.sin(15*a+.445*3)
        z=.445+.014*math.sin(3*a+.6)+.008*math.sin(7*a+1.2)+max(0,-math.cos(a))**8*.012
        hem.append(((.119+d)*math.cos(a),(.220+d)*math.sin(a),z+.003))
    tube('Irregular doubled coat hem',hem,.0035,'Leather',True)
    for yy in [-.112,.112]:
        tube('Long stitched coat back seam',[(-.111,yy,.465),(-.135,yy,.64),(-.143,yy,.77),(-.133,yy,.93),(-.148,yy,1.19),(-.138,yy,1.36)],.0020,'Canvas')
    # Overlapping back vent with non-straight edges breaks the rigid skirt silhouette.
    tube('Coat rear split-vent binding',[(-.128,-.006,.451),(-.141,-.005,.527),(-.146,-.003,.646),(-.153,0,.755),(-.148,.005,.840)],.0025,'Canvas')
    for sy in [-1,1]:
        tube('Coat vertical flap',[(.108,sy*.110,.47),(.141,sy*.078,.70),(.145,sy*.056,.9),(.147,sy*.034,1.10),(.162,sy*.032,1.29),(.120,sy*.035,1.45)],.004,'Leather')
        # Soft hanging utility pouch, integrated rounded shape.
        soft_box('Worn belt utility pouch',(-.024,sy*.191,.935),(.050,.034,.090),'Canvas',.0025)
        tube('Pouch flap seam',[(-.10,sy*.245,.971),(-.032,sy*.252,.952),(.029,sy*.245,.971)],.004,'Rust')
    loft_z('Heavy waist belt',[(.997,0,0,.144,.193),(1.026,0,0,.143,.192),(1.047,0,0,.143,.191)],'Leather',64)
    for yy in [-.151,.151]:
        ribbon('Broad woven shoulder harness',[(-.158,yy,1.036),(-.169,yy,1.229),(-.112,yy,1.416),(.004,yy,1.449),(.134,yy,1.297),(.142,yy,1.084)],.031,'Canvas')
        buckle('Harness adjustment buckle',-.171,yy,1.116,.036,.033)
    # Raised scarf/hood collar; rear folds visibly merge into the shoulders.
    collar=[]
    for j in range(31):
        t=j/30;z=1.435+t*.162
        collar.append((z,-.014-.015*math.sin(t*math.pi),0,.119-.026*t+.012*math.sin(t*math.pi),.156-.050*t+.009*math.sin(t*math.pi)))
    cowl=loft_z('Soft irregular folded storm collar',collar,'Cloth',96,.007,caps=False)
    for v in cowl.data.vertices:
        a=math.atan2(v.co.y,v.co.x+.02)
        t=max(0,min(1,(v.co.z-1.435)/.162))
        v.co.z+=t*(.014*math.cos(a)-.014*max(0,-math.cos(a))+.005*math.sin(a*3+.7))
    sol=cowl.modifiers.new('Storm collar doubled cloth','SOLIDIFY');sol.thickness=.004
    for j in range(2):
        z=1.472+j*.033
        tube('Loose scarf fold',[(-.021,-.133+j*.007,z+.038),(-.115,-.108+j*.010,z+.005),(-.139,0,z-.017),(-.116,.107-j*.009,z-.002),(-.012,.134-j*.010,z+.039)],.005-j*.0005,'Cloth')
    hood=ellipsoid('Folded half hood draped across shoulders',(-.097,.002,1.485),(.069,.129,.055),'Cloth',64,36)
    for v in hood.data.vertices:
        a=math.atan2(v.co.y,v.co.x)
        v.co.z+=.044*math.sin(a*5+v.co.z*3)
    tube('Half hood bound edge',[(-.006,-.112,1.530),(-.094,-.115,1.532),(-.157,-.005,1.494),(-.104,.121,1.523),(-.005,.119,1.525)],.0032,'Canvas')
    # Head is helmeted and masked; the rear view does not rely on a face texture.
    ellipsoid('Cloth balaclava head',(.009,0,1.655),(.088,.078,.103),'Cloth',64,40)
    ellipsoid('Worn low steel work helmet',(.003,0,1.701),(.098,.091,.077),'DarkSteel',64,36)
    ring('Helmet lower rim',(-.006,0,1.668),.105,.095,'Leather',.005)
    tube('Helmet flattened centre seam',[(-.094,0,1.697),(-.051,0,1.755),(.010,0,1.778),(.071,0,1.744),(.096,0,1.701)],.0018,'Rust')
    for sy in [-1,1]:
        ribbon('Work helmet leather retaining band',[(-.085,sy*.035,1.709),(-.05,sy*.063,1.740),(.013,sy*.066,1.755),(.079,sy*.046,1.725)],.014,'Leather',side=(0,1,0),thickness=.0016)
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
            keys=[(0,sy*.222,1.411,.083),(-.004,sy*.255,1.331,.087),(-.037,sy*.279,1.214,.078),(-.030,sy*.290,1.112,.074),(.027,sy*.322,1.011,.059),(.052,sy*.341,.936,.048)]
        limb('Loose bent coat sleeve with elbow gathering',keys,wrinkles=.009,oval=.96)
        wrist=keys[-1][:3];wrists[sy]=wrist
        prev=Vector(keys[-2][:3]);end=Vector(wrist)
        limb('Soft reinforced work sleeve cuff',[(*prev,.060),(*(prev.lerp(end,.7)),.056),(*end,.051)],'Leather',.004)
        glove(wrist,stop and sy==1)
        shoulder_plate(sy*.226)
        elbow=keys[3][:3]
        ellipsoid('Soft stitched elbow reinforcement',Vector(elbow)+Vector((-.058,0,0)),(.009,.057,.067),'Canvas',36,24)
        for j in range(4):
            zz=elbow[2]+.01+j*.022
            tube('Compressed elbow cloth edge',[(elbow[0]-.020,elbow[1]-sy*.053,zz+.006),(elbow[0]-.080,elbow[1],zz),(elbow[0]-.022,elbow[1]+sy*.050,zz-.007)],.0025,'Cloth')
    worn_pack()
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
    # A small forward lean from the hips and weighted, relaxed shoulder posture.
    def pose_point(p):
        p=Vector(p)
        p.x+=max(0,p.z-.78)*.084
        p.y+=.005*math.sin(max(0,p.z-.28)*2.8)
        return p
    for v in obj.data.vertices:v.co=pose_point(v.co)
    light_local=list(pose_point(light_local))
    # UV0 is regenerated from the finished geometry. Average island scale removes the
    # old mixed primitive densities; the final area normalization makes one UV square
    # correspond to approximately one square metre of surface. Tiling is intentional.
    for layer in list(obj.data.uv_layers):obj.data.uv_layers.remove(layer)
    obj.data.uv_layers.new(name='UV0_Tile1m')
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.018,correct_aspect=True,scale_to_bounds=False)
    bpy.ops.uv.select_all(action='SELECT')
    bpy.ops.uv.average_islands_scale()
    bpy.ops.object.mode_set(mode='OBJECT')
    obj.data.calc_loop_triangles()
    uv_data=obj.data.uv_layers.active.data
    uv_area=0.0
    for tri in obj.data.loop_triangles:
        a,b,c=[uv_data[i].uv for i in tri.loops]
        uv_area+=abs((b.x-a.x)*(c.y-a.y)-(b.y-a.y)*(c.x-a.x))*.5
    surface_area=sum(p.area for p in obj.data.polygons)
    uv_scale=math.sqrt(surface_area/max(1e-10,uv_area))
    for loop in uv_data:loop.uv*=uv_scale
    rotation=Matrix.Rotation(math.radians(yaw),4,'Z')
    offset=Vector(origin)
    for v in obj.data.vertices:v.co=rotation@v.co+offset
    # Source UV0 is a surface-material tiling layer; let UE generate a separate lightmap.
    for p in obj.data.polygons:p.use_smooth=True
    obj.data.update()
    bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
    obj['asset_role']='static posed expedition worker, original procedural mesh'
    obj['source_forward_axis']='X'
    obj['source_length_unit']='metre'
    obj['requires_material_binding']='Cloth,DarkSteel,Rust,Amber,Leather,Canvas'
    bpy.ops.export_scene.fbx(filepath=str(OUT/(name+'.fbx')),use_selection=True,object_types={'MESH'},use_mesh_modifiers=True,mesh_smooth_type='FACE',use_triangles=True,add_leaf_bones=False,bake_anim=False,axis_forward='-Y',axis_up='Z',global_scale=1.0,apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',use_custom_props=True)
    triangulated=sum(max(0,len(p.vertices)-2) for p in obj.data.polygons)
    bounds=[[min(v.co[i] for v in obj.data.vertices) for i in range(3)],[max(v.co[i] for v in obj.data.vertices) for i in range(3)]]
    return {'name':name,'fbx':name+'.fbx','origin_m':[0,0,0],'placement_baked_m':origin,'yaw_baked_deg':yaw,'bounds_m':bounds,'triangles':triangulated,'vertices':len(obj.data.vertices),'lantern_center_m':list(rotation@Vector(light_local)+offset),'material_slots':list(MATERIALS),'uv0':{'layer':'UV0_Tile1m','purpose':'surface textures, tiling permitted','metres_per_uv_unit_approx':1,'surface_area_m2':surface_area,'normalized_uv_area':uv_area*uv_scale**2,'texture_0254m_repeat_multiplier':1/.254},'pose':'slight forward lean; right hand stop gesture, left hand lantern' if stop else 'slight forward lean; relaxed elbows; right hand lantern'}


entries=[build_figure('SM_Expedition_Protagonist',[0,-.6,0],0),build_figure('SM_Expedition_Companion',[7,-.4,0],-18,True)]
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'ExpeditionFigures.blend'))
manifest={'asset_version':2,'generator':'build_expedition_figures.py','blender_version':bpy.app.version_string,'authorship':'Original procedural geometry made for Ash Well; no downloaded assets','purpose':'Worn industrial static figures for the UE visual sample; not rigged or animation ready','changes_from_v1':['Forward hip lean and relaxed curved sleeves','Thick irregular storm collar and half hood hide the smooth rear neck','Larger nonuniform folds at elbows, knees, waist and skirt; worn bound edges','Small close shoulder reinforcements replace round pauldrons','Old rectangular canvas pack, broad webbing, straps, buckles, bedroll and tools replace twin exposed tanks','One compact oxygen bottle in a canvas sleeve','Curled gloved fingers close around the lantern bail','UV0 unified near one metre per UV unit for surface material tiling'],'source_coordinates':'Metres, +X forward, +Y right, +Z up; each object origin is world zero and placement is baked into vertices','fbx_export':{'axis_forward':'-Y','axis_up':'Z','global_scale':1.0,'apply_unit_scale':True,'apply_scale_options':'FBX_SCALE_UNITS','unit_settings_scale_length':1.0,'notes':'FBX carries metre units. UE scene-unit conversion should yield centimetres. Verify the imported height is about 178 cm, facing +X, before enabling any Force Front X Axis override. Both actors should be placed at world origin when preserving baked positions.'},'material_parameters':{n:{'base_color':list(m.diffuse_color[:3]),'role':'emissive glass, bind an Unreal emissive material and add a point light using lantern_center_m' if n=='Amber' else n} for n,m in MATERIALS.items()},'assets':entries,'total_triangles':sum(e['triangles'] for e in entries)}
(OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
print('ASH_WELL_CHARACTER_MANIFEST '+json.dumps(manifest,ensure_ascii=False))
