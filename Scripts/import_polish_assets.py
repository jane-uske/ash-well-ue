import unreal as u,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];ed=u.EditorAssetLibrary;tools=u.AssetToolsHelpers.get_asset_tools()
for item in json.loads((ROOT/'SourceAssets/PolishAudio/manifest.json').read_text()):
 path=ROOT/'SourceAssets/PolishAudio'/item['file'];name=path.stem
 t=u.AssetImportTask();t.filename=str(path);t.destination_path='/Game/AshWell/Combat/Polish';t.destination_name=name
 t.automated=True;t.replace_existing=True;t.save=True;t.factory=u.SoundFactory();tools.import_asset_tasks([t])
 sound=ed.load_asset(t.destination_path+'/'+name);assert isinstance(sound,u.SoundWave)
 sound.set_editor_property('looping',item['loop']);ed.save_loaded_asset(sound)
for n in ['M_WardenHQ','M_WardenHQ_Inner']:
 mat=ed.load_asset('/Game/AshWell/Combat/WardenHQ/'+n);mat.set_editor_property('used_with_skeletal_mesh',True)
 u.MaterialEditingLibrary.recompile_material(mat);ed.save_loaded_asset(mat)
u.log('ASHWELL_POLISH_ASSETS_IMPORTED')
