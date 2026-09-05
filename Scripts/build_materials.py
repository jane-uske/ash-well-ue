"""Import the attributed CC0 texture set and build editable UE PBR materials."""
import json
import pathlib
import unreal as u

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / 'SourceAssets/Textures'
BASE = '/Game/AshWell'
tools = u.AssetToolsHelpers.get_asset_tools()
ed = u.EditorAssetLibrary
mel = u.MaterialEditingLibrary
manifest = json.loads((SRC / 'manifest.json').read_text())

def constant(mat, value):
    n = mel.create_material_expression(mat, u.MaterialExpressionConstant)
    n.set_editor_property('r', value)
    return n

def color(mat, value):
    n = mel.create_material_expression(mat, u.MaterialExpressionConstant3Vector)
    n.set_editor_property('constant', u.LinearColor(*value))
    return n

def prop(node, dest):
    assert mel.connect_material_property(node, '', dest)

def connect(a, b, pin):
    assert mel.connect_material_expressions(a, '', b, pin)

def fresh_mat(name):
    path = BASE + '/Materials/' + name
    mat = ed.load_asset(path)
    if not mat:
        mat = tools.create_asset(name, BASE + '/Materials', u.Material, u.MaterialFactoryNew())
    mel.delete_all_material_expressions(mat)
    return mat

for source in manifest['materials']:
    name = source['material_name']
    mat = fresh_mat(name)
    uv = mel.create_material_expression(mat, u.MaterialExpressionTextureCoordinate)
    tile = source['tile_size_m']
    if isinstance(tile, list):
        tile = tile[0]
    uv.set_editor_property('u_tiling', 1.0 / tile)
    uv.set_editor_property('v_tiling', 1.0 / tile)
    for channel, spec in source['textures'].items():
        file = SRC / spec['path']
        asset_name = 'T_' + source['id'] + '_' + channel
        dest = BASE + '/Textures/' + asset_name
        tex = ed.load_asset(dest)
        if not tex:
            task = u.AssetImportTask()
            task.filename = str(file)
            task.destination_path = BASE + '/Textures'
            task.destination_name = asset_name
            task.automated = True
            task.save = True
            task.factory = u.TextureFactory()
            tools.import_asset_tasks([task])
            tex = ed.load_asset(dest)
        if not tex:
            raise RuntimeError('Texture import failed: ' + str(file))
        tex.set_editor_property('srgb', channel == 'base_color')
        if channel == 'normal':
            tex.set_editor_property('compression_settings', u.TextureCompressionSettings.TC_NORMALMAP)
            tex.set_editor_property('flip_green_channel', False)
        elif channel == 'roughness':
            tex.set_editor_property('compression_settings', u.TextureCompressionSettings.TC_MASKS)
        ed.save_loaded_asset(tex)
        sample = mel.create_material_expression(mat, u.MaterialExpressionTextureSample)
        sample.set_editor_property('texture', tex)
        sample.set_editor_property('sampler_type', {'normal': u.MaterialSamplerType.SAMPLERTYPE_NORMAL, 'roughness': u.MaterialSamplerType.SAMPLERTYPE_MASKS, 'base_color': u.MaterialSamplerType.SAMPLERTYPE_COLOR}[channel])
        connect(uv, sample, 'UVs')
        if channel == 'base_color':
            mul = mel.create_material_expression(mat, u.MaterialExpressionMultiply)
            connect(sample, mul, 'A')
            tint = {'M_Rock': (0.42, 0.48, 0.5), 'M_Rust': (0.50, 0.38, 0.28), 'M_Concrete': (0.48, 0.51, 0.51)}[name]
            connect(color(mat, tint), mul, 'B')
            prop(mul, u.MaterialProperty.MP_BASE_COLOR)
        elif channel == 'normal':
            prop(sample, u.MaterialProperty.MP_NORMAL)
        else:
            mul = mel.create_material_expression(mat, u.MaterialExpressionMultiply)
            connect(sample, mul, 'A')
            connect(constant(mat, 0.72 if name != 'M_Rust' else 0.92), mul, 'B')
            prop(mul, u.MaterialProperty.MP_ROUGHNESS)
    prop(constant(mat, 0.0), u.MaterialProperty.MP_METALLIC)
    mel.layout_material_expressions(mat)
    mel.recompile_material(mat)
    ed.save_loaded_asset(mat)

for name, rgb, rough, metal in [
    ('M_DarkSteel', (0.035, 0.045, 0.048), 0.44, 0.78),
    ('M_Cloth', (0.032, 0.042, 0.039), 0.95, 0.0),
    ('M_Leather', (0.040, 0.026, 0.016), 0.68, 0.0),
    ('M_Amber', (1.0, 0.30, 0.055), 0.30, 0.0),
]:
    mat = fresh_mat(name)
    prop(color(mat, rgb), u.MaterialProperty.MP_BASE_COLOR)
    prop(constant(mat, rough), u.MaterialProperty.MP_ROUGHNESS)
    prop(constant(mat, metal), u.MaterialProperty.MP_METALLIC)
    if name == 'M_Amber':
        prop(color(mat, (5.0, 1.30, 0.18)), u.MaterialProperty.MP_EMISSIVE_COLOR)
    mel.layout_material_expressions(mat)
    mel.recompile_material(mat)
    ed.save_loaded_asset(mat)

u.log('ASHWELL: 7 PBR materials prepared')
