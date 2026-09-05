from pathlib import Path
root=Path(__file__).resolve().parents[1]
source=(root/'Scripts/build_v2_materials.py').read_text()
exec(compile(source.split("src=ROOT/'SourceAssets/SurfaceV2'")[0],str(root/'Scripts/build_v2_materials.py'),'exec'))
src=ROOT/'SourceAssets/Textures'
concrete=next(s for s in json.loads((src/'manifest.json').read_text())['materials'] if s['material_name']=='M_Concrete')
pbr('Concrete',src,concrete,.75,(.42,.45,.45),.75,.60,.22,macro=True)
