import json
from pathlib import Path
import unreal as u
root=Path(__file__).resolve().parents[1]
sub=u.get_editor_subsystem(u.StaticMeshEditorSubsystem)
data={}
for name in ['get_nanite_settings','set_nanite_settings']:
    data[name]=str(getattr(sub,name,None).__doc__)
data['nanite_settings_doc']=str(u.MeshNaniteSettings.__doc__) if hasattr(u,'MeshNaniteSettings') else [n for n in dir(u) if 'Nanite' in n]
data['nanite_enabled']=u.SystemLibrary.get_console_variable_int_value('r.Nanite')
(root/'Saved/Automation/v2-render-api.json').write_text(json.dumps(data,indent=2))
