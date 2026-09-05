"""Original irregular stone deck for Ash Well's second visual iteration.

Blender --background --python build_surface_v2.py
Geometry matches SourceAssets/Geometry/build_environment.py route(t).
Metres, +X forward, +Y right, +Z up, common origin zero. No UE actions.
"""
import bpy, bmesh, math, random, json, hashlib
from pathlib import Path
from mathutils import Vector, noise

ROOT = Path(__file__).resolve().parent
RNG = random.Random(731904)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
bpy.context.scene.unit_settings.system='METRIC'
bpy.context.scene.unit_settings.scale_length=1.0
SLOTS=['WetStone','Debris','DarkSteel']
COLORS=[(.115,.125,.128,1),(.055,.056,.052,1),(.045,.052,.055,1)]
MATS=[]
for name,color in zip(SLOTS,COLORS):
    m=bpy.data.materials.new(name);m.diffuse_color=color;m.use_nodes=True
    bsdf=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    bsdf.inputs['Base Color'].default_value=color
    bsdf.inputs['Roughness'].default_value=.38 if name=='WetStone' else (.76 if name=='Debris' else .52)
    bsdf.inputs['Metallic'].default_value=.65 if name=='DarkSteel' else 0
    MATS.append(m)

def route(t):
    if t<=12:return Vector((-6+t,0,0))
    q=(t-12)/20
    return Vector((6+18*q,8*q*q*(3-2*q),0))

def frame(t):
    p=route(t)
    tangent=(route(min(32,t+.025))-route(max(0,t-.025))).normalized()
    return p,tangent,Vector((-tangent.y,tangent.x,0))

def world(u,v,z):
    p,t,s=frame(u)
    return p+s*v+Vector((0,0,z))

def clip(poly,nx,ny,d):
    """Keep nx*x+ny*y<=d for a convex polygon."""
    if not poly:return []
    result=[]
    prev=poly[-1];pa=nx*prev[0]+ny*prev[1]-d
    for cur in poly:
        ca=nx*cur[0]+ny*cur[1]-d
        if (ca<=0)!=(pa<=0):
            t=pa/(pa-ca)
            result.append((prev[0]+t*(cur[0]-prev[0]),prev[1]+t*(cur[1]-prev[1])))
        if ca<=0:result.append(cur)
        prev=cur;pa=ca
    return result

class Build:
    def __init__(self,name):
        self.name=name;self.v=[];self.f=[];self.mi=[];self.colors=[]
    def add(self,verts,faces,slot='WetStone',color=(1,1,1,.5)):
        n=len(self.v)
        self.v.extend([tuple(v) for v in verts]);self.colors.extend([color]*len(verts))
        self.f.extend([tuple(n+x for x in f) for f in faces]);self.mi.extend([SLOTS.index(slot)]*len(faces))
    def finish(self):
        mesh=bpy.data.meshes.new(self.name);mesh.from_pydata(self.v,[],self.f);mesh.update()
        obj=bpy.data.objects.new(self.name,mesh);bpy.context.collection.objects.link(obj)
        for mat in MATS:mesh.materials.append(mat)
        for face,mi in zip(mesh.polygons,self.mi):face.material_index=mi
        # Store modest per-stone color and wetness variation for UE material use.
        col=mesh.color_attributes.new(name='Color',type='FLOAT_COLOR',domain='POINT')
        for item,value in zip(col.data,self.colors):item.color=value
        bm=bmesh.new();bm.from_mesh(mesh)
        bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
        for face in bm.faces:face.smooth=True
        for edge in bm.edges:
            if len(edge.link_faces)==2:edge.smooth=edge.calc_face_angle(0)<math.radians(38)
        bm.to_mesh(mesh);bm.free();mesh.update()
        uv=mesh.uv_layers.new(name='UVMap')
        for face in mesh.polygons:
            axis=max(range(3),key=lambda k:abs(face.normal[k]))
            axes=[k for k in range(3) if k!=axis]
            for li in face.loop_indices:
                p=mesh.vertices[mesh.loops[li].vertex_index].co
                uv.data[li].uv=(p[axes[0]],p[axes[1]])
        mesh.calc_loop_triangles()
        bounds={'min':[round(min(v.co[k] for v in mesh.vertices),6) for k in range(3)],
                'max':[round(max(v.co[k] for v in mesh.vertices),6) for k in range(3)]}
        bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj
        path=ROOT/(self.name+'.fbx')
        bpy.ops.export_scene.fbx(filepath=str(path),use_selection=True,object_types={'MESH'},
            global_scale=1.0,apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',
            axis_forward='-Y',axis_up='Z',use_space_transform=True,bake_space_transform=False,
            mesh_smooth_type='EDGE',use_mesh_modifiers=True,use_triangles=True,
            add_leaf_bones=False,bake_anim=False,path_mode='AUTO',colors_type='LINEAR')
        result={'name':self.name,'file':path.name,'vertices':len(mesh.vertices),'triangles':len(mesh.loop_triangles),
                'origin_m':[0,0,0],'bounds_m':bounds,'material_slots':SLOTS,
                'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'uv_metres_per_unit':1,
                'vertex_color':'RGB = restrained stone value variation, A = wetness amount (0..1).'}
        obj.select_set(False)
        print('EXPORTED',json.dumps(result),flush=True)
        return result

deck=Build('SM_SurfaceV2_BrokenStoneDeck')
mortar=Build('SM_SurfaceV2_MortarAndDebris')
details=Build('SM_SurfaceV2_SteelRepairs')

# Mortar/substrate fills narrow interstices and terminates below the existing top
# of the old deck. Its edges are chipped, not a bright uninterrupted flat slab.
nu=281;nv=25
verts=[]
for i in range(nu):
    u=4+28*i/(nu-1)
    for j in range(nv):
        v=-1.475+2.95*j/(nv-1)
        z=-.038+.0025*noise.noise(Vector((u*2.5,v*2.5,11)))
        verts.append(world(u,v,z))
faces=[]
for i in range(nu-1):
    for j in range(nv-1):
        a=i*nv+j;faces.append((a,a+nv,a+nv+1,a+1))
mortar.add(verts,faces,'Debris',(.8,.82,.79,.82))

# Irregular seed placement with no aligned transverse rows. Voronoi adjacency
# keeps substantial flat walkable pieces, and a subset is split into two shards.
seeds=[]
attempts=0
while len(seeds)<382 and attempts<12000:
    attempts+=1
    p=(RNG.uniform(3.83,32.17),RNG.uniform(-1.66,1.66))
    minimum=RNG.uniform(.265,.37)
    if all((p[0]-q[0])**2+(p[1]-q[1])**2>minimum**2 for q in seeds):seeds.append(p)

cells=[]
for i,p in enumerate(seeds):
    poly=[(4,-1.47),(32,-1.47),(32,1.47),(4,1.47)]
    neighbors=sorted([q for j,q in enumerate(seeds) if j!=i],key=lambda q:(p[0]-q[0])**2+(p[1]-q[1])**2)[:32]
    for q in neighbors:
        nx=q[0]-p[0];ny=q[1]-p[1]
        poly=clip(poly,nx,ny,(q[0]**2+q[1]**2-p[0]**2-p[1]**2)/2)
        if len(poly)<3:break
    if len(poly)<3:continue
    area=abs(sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(poly,poly[1:]+poly[:1])))/2
    if area<.014:continue
    if RNG.random()<.16 and area>.17:
        ang=RNG.uniform(0,math.tau);nx=math.cos(ang);ny=math.sin(ang)
        cx=sum(v[0] for v in poly)/len(poly);cy=sum(v[1] for v in poly)/len(poly)
        d=nx*cx+ny*cy+RNG.uniform(-.035,.035)
        parts=[clip(poly,nx,ny,d-.004),clip(poly,-nx,-ny,-d-.004)]
        cells.extend([p for p in parts if len(p)>=3])
    else:cells.append(poly)

stone_top_min=1;stone_top_max=-1
for index,poly in enumerate(cells):
    cx=sum(p[0] for p in poly)/len(poly);cy=sum(p[1] for p in poly)/len(poly)
    # Most joints are 8-18 mm; occasional fractured patches have wider gaps.
    gap=RNG.uniform(.004,.009)*(1.8 if index%17==0 else 1)
    trimmed=[]
    for p in poly:
        dx=p[0]-cx;dy=p[1]-cy;r=math.hypot(dx,dy)
        s=max(.76,1-gap/max(r,.025));trimmed.append((cx+dx*s,cy+dy*s))
    # Resample and chip the perimeter. Top rings retain large flat areas instead
    # of introducing faceted piles or tall cobbles under the figures' feet.
    boundary=[]
    for a,b in zip(trimmed,trimmed[1:]+trimmed[:1]):
        length=math.dist(a,b);count=max(1,math.ceil(length/.09))
        for j in range(count):
            t=j/count;u=a[0]+t*(b[0]-a[0]);v=a[1]+t*(b[1]-a[1])
            chip=RNG.uniform(0,.006)
            if j and RNG.random()<.1:chip+=RNG.uniform(.008,.022)
            r=max(math.hypot(u-cx,v-cy),.01)
            boundary.append((u+(cx-u)*chip/r,v+(cy-v)*chip/r))
    n=len(boundary)
    if n<3:continue
    offset=RNG.uniform(-.009,.004)
    tilt_x=RNG.uniform(-.009,.009);tilt_y=RNG.uniform(-.009,.009)
    wetness=.3+.55*(.5+.5*noise.noise(Vector((cx*.7,cy*1.9,14))))
    shade=RNG.uniform(.77,1.02)
    tint=(shade,shade*RNG.uniform(.975,1.015),shade*RNG.uniform(.965,1.025),wetness)
    def height(u,v):
        z=-.012+offset+tilt_x*(u-cx)+tilt_y*(v-cy)
        z+=.0032*noise.noise(Vector((u*11,v*11,4)))+.001*noise.noise(Vector((u*35,v*35,7)))
        # Standing figures retain their approved ground height near z=0.
        x=-6+u if u<=12 else 6+18*(u-12)/20
        if (x*x+(v+.6)**2<.8**2) or ((x-7)**2+(v+.4)**2<.65**2):z=min(z,-.005)
        return min(.004,z)
    vs=[]
    for scale,lower in [(1,-.01),(.967,0),(.72,0),(.40,0),(.15,0)]:
        for u,v in boundary:
            u=cx+(u-cx)*scale;v=cy+(v-cy)*scale
            z=height(u,v)+lower
            stone_top_min=min(stone_top_min,z);stone_top_max=max(stone_top_max,z)
            vs.append(world(u,v,z))
    center_idx=len(vs);vs.append(world(cx,cy,height(cx,cy)))
    bottom_idx=len(vs)
    for u,v in boundary:vs.append(world(u,v,-.078+offset))
    fs=[]
    for r in range(4):
        for j in range(n):
            k=(j+1)%n;a=r*n+j;b=r*n+k;c=(r+1)*n+k;d=(r+1)*n+j
            if j%2:fs.extend([(a,b,d),(b,c,d)])
            else:fs.extend([(a,b,c),(a,c,d)])
    for j in range(n):
        k=(j+1)%n;fs.append((4*n+j,4*n+k,center_idx))
        fs.append((bottom_idx+j,bottom_idx+k,k,j))
    fs.append(tuple(reversed(range(bottom_idx,bottom_idx+n))))
    deck.add(vs,fs,'WetStone',tint)

# Small angular chips and compressed gravel are biased to the gutters. A clear
# centre path and the two standing areas are preserved.
pebbles=0
for i in range(310):
    u=RNG.uniform(4,32)
    v=RNG.choice([-1,1])*RNG.uniform(1.12,1.435) if RNG.random()<.82 else RNG.uniform(-1.35,1.35)
    p=world(u,v,0)
    if (p.x*p.x+(p.y+.6)**2<.85**2) or ((p.x-7)**2+(p.y+.4)**2<.75**2):continue
    rad=RNG.uniform(.017,.059)
    if abs(v)>1.26 and RNG.random()<.22:rad=RNG.uniform(.065,.115)
    bm=bmesh.new();bmesh.ops.create_icosphere(bm,subdivisions=1,radius=1)
    bm.verts.ensure_lookup_table();bm.verts.index_update()
    phi=RNG.uniform(0,math.tau);co=math.cos(phi);si=math.sin(phi)
    vs=[]
    for vert in bm.verts:
        q=vert.co;r=1+RNG.uniform(-.2,.2)
        x=q.x*rad*r;y=q.y*rad*RNG.uniform(.65,1.1)
        vs.append(p+Vector((x*co-y*si,x*si+y*co,-.019+q.z*rad*.36)))
    fs=[tuple(v.index for v in f.verts) for f in bm.faces];bm.free()
    shade=RNG.uniform(.6,1.05)
    mortar.add(vs,fs,'Debris',(shade,shade*.985,shade*.95,.48));pebbles+=1

# A few modest repair straps, mostly at the edge, preserve the industrial origin
# without restoring the previous large shiny regular metal floor rectangles.
for u,v,angle in [(8.1,1.24,.38),(14.8,-1.18,-.5),(24.1,1.24,.23)]:
    p,t,s=frame(u);center=p+s*v
    axis=(t*math.cos(angle)+s*math.sin(angle)).normalized();side=Vector((-axis.y,axis.x,0))
    vs=[]
    for z in [-.024,-.014]:
        for sy in [-1,1]:
            for sx in [-1,1]:vs.append(center+axis*(sx*.23)+side*(sy*.031)+Vector((0,0,z)))
    details.add(vs,[(0,2,3,1),(4,5,7,6),(0,1,5,4),(2,6,7,3),(0,4,6,2),(1,3,7,5)],'DarkSteel',(.75,.79,.8,.25))
    for sx in [-.17,.17]:
        c=center+axis*sx
        vs=[]
        for z,r in [(-.013,.015),(-.006,.014)]:
            for j in range(8):vs.append(c+Vector((r*math.cos(j*math.tau/8),r*math.sin(j*math.tau/8),z)))
        fs=[tuple(reversed(range(8))),tuple(range(8,16))]+[(j,(j+1)%8,(j+1)%8+8,j+8) for j in range(8)]
        details.add(vs,fs,'DarkSteel',(.85,.85,.85,.2))

entries=[x.finish() for x in [deck,mortar,details]]
assert sum(e['triangles'] for e in entries)<500000
manifest={'schema_version':2,'generator':'build_surface_v2.py','authorship':'Original procedural geometry generated for Ash Well; no downloaded meshes.',
 'texture_manifest':'texture_manifest.json','source_units':'metres','source_axes':{'forward':'+X','right':'+Y','up':'+Z'},
 'route':'Same route(t) as Geometry/build_environment.py; t=4..32, centreline x=-2..24, width=2.94m inside existing 3m edge structure.',
 'material_slots':SLOTS,'recommended_material_bindings':{
  'WetStone':{'texture_material':'WetStone','uv_multiplier':.5,'base_color_desaturation':.8,'base_color_multiplier':[.42,.46,.49],'metallic':0,'roughness_range':[.26,.70],'normal_strength':.65,'note':'Vertex RGB supplies subtle slab variation; vertex alpha optional wetness. Avoid uniform mirror roughness.'},
  'Debris':{'texture_material':'WetStone','uv_multiplier':.65,'base_color_desaturation':.85,'base_color_multiplier':[.22,.24,.23],'metallic':0,'roughness':.76,'normal_strength':.45},
  'DarkSteel':{'texture_material':'OldSteel','uv_multiplier':.5,'base_color_desaturation':.7,'base_color_multiplier':[.3,.32,.34],'metallic':'Use blue channel of ARM texture','roughness_range':[.42,.82]}},
 'import':{'place_all_actors_at':[0,0,0],'rotation':[0,0,0],'scale':[1,1,1],'convert_scene_unit':True,'mesh_origin_m':[0,0,0],'parent_handles_y_mirror':True,'fbx_axis_forward':'-Y','fbx_axis_up':'Z','vertex_color_import':'REPLACE','replace_old_actor':'SM_WalkwayDeck only; retain edge beams, rails and truss.'},
 'stone_pieces':len(cells),'loose_chips':pebbles,'slab_surface_range_m':[round(stone_top_min,6),round(stone_top_max,6)],
 'standing_areas':'Around protagonist x=0,y=-0.6 and companion x=7,y=-0.4 slabs remain at/below z=-0.005; no upward actor translation required.',
 'assets':entries,'total_triangles':sum(e['triangles'] for e in entries)}
(ROOT/'surface_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'AshWell_SurfaceV2_Source.blend'))
print('COMPLETE',json.dumps({'stones':len(cells),'chips':pebbles,'triangles':manifest['total_triangles']}),flush=True)
