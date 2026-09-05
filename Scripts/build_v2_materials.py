"""V2 scanned surfaces; all materials live separately from the first study."""
import json
from pathlib import Path
import unreal as u
ROOT=Path(__file__).resolve().parents[1]
BASE='/Game/AshWell'
ed=u.EditorAssetLibrary
tools=u.AssetToolsHelpers.get_asset_tools()
mel=u.MaterialEditingLibrary

def node(mat, cls): return mel.create_material_expression(mat,cls)
def c(mat,value):
    n=node(mat,u.MaterialExpressionConstant); n.r=value; return n
def color(mat,rgb):
    n=node(mat,u.MaterialExpressionConstant3Vector); n.constant=u.LinearColor(*rgb); return n
def link(a,b,pin): assert mel.connect_material_expressions(a,'',b,pin),pin
def prop(a,p): assert mel.connect_material_property(a,'',p),str(p)
def mul(mat,a,b):
    n=node(mat,u.MaterialExpressionMultiply); link(a,n,'A');link(b,n,'B');return n
def add(mat,a,b):
    n=node(mat,u.MaterialExpressionAdd);link(a,n,'A');link(b,n,'B');return n
def fresh(name):
    m=ed.load_asset(BASE+'/Materials/V2/M_'+name)
    if not m: m=tools.create_asset('M_'+name,BASE+'/Materials/V2',u.Material,u.MaterialFactoryNew())
    mel.delete_all_material_expressions(m);return m
def texture(src,aid,ch,spec):
    name='T_'+aid+'_'+ch
    path=BASE+'/Textures/V2/'+name
    tex=ed.load_asset(path)
    if not tex:
        t=u.AssetImportTask();t.filename=str(src/spec['path']);t.destination_path=BASE+'/Textures/V2';t.destination_name=name
        t.automated=True;t.save=True;t.factory=u.TextureFactory();tools.import_asset_tasks([t]);tex=ed.load_asset(path)
    assert tex,path
    tex.set_editor_property('srgb',ch=='base_color')
    if ch=='normal':
        tex.set_editor_property('compression_settings',u.TextureCompressionSettings.TC_NORMALMAP)
        tex.set_editor_property('flip_green_channel',False)
    elif ch=='roughness':tex.set_editor_property('compression_settings',u.TextureCompressionSettings.TC_MASKS)
    ed.save_loaded_asset(tex);return tex
def pbr(name,src,source,tile,tint,desat,rough_scale,rough_bias,metal=0,macro=False):
    mat=fresh(name)
    uv=node(mat,u.MaterialExpressionTextureCoordinate);uv.u_tiling=tile;uv.v_tiling=tile
    for ch in ['base_color','roughness','normal']:
        tex=texture(src,source['id'],ch,source['textures'][ch])
        s=node(mat,u.MaterialExpressionTextureSample);s.texture=tex
        s.sampler_type={'base_color':u.MaterialSamplerType.SAMPLERTYPE_COLOR,'roughness':u.MaterialSamplerType.SAMPLERTYPE_MASKS,'normal':u.MaterialSamplerType.SAMPLERTYPE_NORMAL}[ch]
        link(uv,s,'UVs')
        if ch=='base_color':
            d=node(mat,u.MaterialExpressionDesaturation)
            inputs=mel.get_material_expression_input_names(d)
            link(s,d,str(inputs[0]));link(c(mat,desat),d,str(inputs[1]))
            base=mul(mat,d,color(mat,tint))
            if macro:
                world=node(mat,u.MaterialExpressionWorldPosition)
                stretched=mul(mat,world,color(mat,(.0035,.0035,.0006)))
                noise=node(mat,u.MaterialExpressionNoise);noise.set_editor_property('scale',1.0)
                noise.set_editor_property('quality',2);noise.set_editor_property('levels',3)
                noise.set_editor_property('output_min',0.0);noise.set_editor_property('output_max',1.0)
                link(stretched,noise,str(mel.get_material_expression_input_names(noise)[0]))
                base=mul(mat,base,add(mat,c(mat,.35),mul(mat,noise,c(mat,.65))))
            prop(base,u.MaterialProperty.MP_BASE_COLOR)
        elif ch=='roughness':prop(add(mat,mul(mat,s,c(mat,rough_scale)),c(mat,rough_bias)),u.MaterialProperty.MP_ROUGHNESS)
        else:prop(s,u.MaterialProperty.MP_NORMAL)
    prop(c(mat,metal),u.MaterialProperty.MP_METALLIC)
    mel.layout_material_expressions(mat);mel.recompile_material(mat);ed.save_loaded_asset(mat)
    u.log('ASHWELL V2 material '+name)

src=ROOT/'SourceAssets/SurfaceV2'
surfaces={m['material_name']:m for m in json.loads((src/'texture_manifest.json').read_text())['materials']}
pbr('WetStone',src,surfaces['WetStone'],.5,(.34,.36,.37),.85,.62,.15)
pbr('Debris',src,surfaces['WetStone'],.5,(.29,.30,.30),.75,.65,.18)
pbr('Cloth',src,surfaces['DarkCloth'],3.937,(.30,.31,.30),.96,.15,.83)
pbr('Canvas',src,surfaces['DarkCloth'],3.937,(.40,.31,.22),1.0,.15,.8)
pbr('OldSteel',src,surfaces['OldSteel'],.5,(.22,.25,.26),.88,.60,.18,.60)
pbr('Rust',src,surfaces['OldSteel'],.5,(.35,.28,.22),.52,.68,.20,.22)
src=ROOT/'SourceAssets/ScansV2'
for s in json.loads((src/'manifest.json').read_text())['assets']:
    pbr('Scan_'+s['id'],src,s,1,(.42,.44,.45),.55,.66,.08)
src=ROOT/'SourceAssets/Textures'
concrete=next(s for s in json.loads((src/'manifest.json').read_text())['materials'] if s['material_name']=='M_Concrete')
pbr('Concrete',src,concrete,.75,(.42,.45,.45),.75,.60,.22,macro=True)
ed.save_directory(BASE+'/Materials/V2',only_if_is_dirty=True,recursive=True)
