import unreal, pathlib, json
root = pathlib.Path(__file__).resolve().parents[1]
names = ['FbxImportUI', 'FbxStaticMeshImportData', 'ExponentialHeightFogComponent', 'PostProcessSettings', 'SkyLightComponent', 'CameraComponent', 'EditorLevelLibrary', 'MaterialExpressionTextureSample', 'StaticMeshEditorSubsystem', 'AutomationLibrary']
out = {}
for name in names:
    cls = getattr(unreal, name)
    out[name] = str(cls.__doc__)
    if name in ['EditorLevelLibrary', 'StaticMeshEditorSubsystem', 'AutomationLibrary']:
        out[name + '_methods'] = '\n'.join(dir(cls))
(root / 'Saved/Automation/api.json').write_text(json.dumps(out, indent=2))
