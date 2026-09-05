"""One-shot editor import for combat clips and original foley; closes this editor."""
import json,traceback
from pathlib import Path
import unreal as u
ROOT=Path(__file__).resolve().parents[1]
result={'state':'running'}
try:
    script=ROOT/'Scripts/import_combat_animations.py'
    exec(compile(script.read_text(),str(script),'exec'),{'__file__':str(script),'__name__':'__main__'})
    tasks=[]
    for source in sorted((ROOT/'SourceAssets/CombatAudio').glob('*.wav')):
        task=u.AssetImportTask();task.filename=str(source);task.destination_path='/Game/AshWell/Combat/Audio'
        task.destination_name=source.stem;task.automated=True;task.replace_existing=True;task.save=True
        task.factory=u.SoundFactory();tasks.append(task)
    u.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)
    result['sounds']=[p for task in tasks for p in task.imported_object_paths]
    assert len(result['sounds'])==3,result
    u.EditorAssetLibrary.save_directory('/Game/AshWell/Combat',only_if_is_dirty=True,recursive=True)
    result['state']='completed'
except Exception:
    result={'state':'failed','error':traceback.format_exc()};u.log_error(result['error'])
(ROOT/'Saved/Automation/combat-assets-report.json').write_text(json.dumps(result,indent=2))
u.SystemLibrary.quit_editor()
