"""Export existing evaluated UE horse sequences for offline animation authoring."""
import unreal as u
from pathlib import Path
import json,traceback
R=Path(__file__).resolve().parents[1];O=R/'SourceAssets/MountedReferenceProduction/HorseSource';O.mkdir(parents=True,exist_ok=True)
report={}
try:
    for name in ['Idle','Walk','Gallop']:
        asset=u.EditorAssetLibrary.load_asset('/Game/AshWell/Combat/MountedChargeSample/HorseRetargetConnected/A_IKSampleHorse_'+name)
        assert asset,name
        task=u.AssetExportTask();task.object=asset;task.filename=str(O/(name+'.fbx'))
        task.automated=True;task.prompt=False;task.replace_identical=True
        task.exporter=u.AnimSequenceExporterFBX();task.options=u.FbxExportOption()
        assert u.Exporter.run_asset_export_task(task),name
        report[name]={'seconds':asset.get_editor_property('sequence_length'),'bytes':Path(task.filename).stat().st_size,'source':asset.get_path_name()}
    report['passed']=True
except Exception:
    report['passed']=False;report['error']=traceback.format_exc();u.log_error(report['error'])
finally:
    (O/'export.json').write_text(json.dumps(report,indent=2));u.log('REFERENCE_GAIT_EXPORT '+json.dumps(report));u.SystemLibrary.quit_editor()
