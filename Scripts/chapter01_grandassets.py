from pathlib import Path
import unreal as u,json
R=Path(__file__).resolve().parents[1]
t=u.AssetImportTask();t.filename=str(R/'SourceAssets/SunoWarden/AW_Suno_Warden_Combat.wav');t.destination_path='/Game/AshWell/Combat/GrandEncounter';t.destination_name='AW_Suno_Warden_Combat';t.automated=True;t.save=True;t.replace_existing=True
u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])
s=u.EditorAssetLibrary.load_asset(t.destination_path+'/'+t.destination_name);assert s
s.set_editor_property('looping',True);u.EditorAssetLibrary.save_loaded_asset(s)
report={'ok':True,'sound':s.get_path_name(),'duration':s.get_editor_property('duration'),'use':'Non-commercial prototype, Suno Free trial download'}
(R/'Saved/GrandEncounter/music-import.json').write_text(json.dumps(report,indent=2))
