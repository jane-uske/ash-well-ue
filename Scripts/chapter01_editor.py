import sys,json,os
from pathlib import Path
import unreal as u
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'Scripts'))
import chapter01_tools
from toolset_registry.registration import Registration
registration=Registration([chapter01_tools.ChapterOneTools]);registration.register()
u.EditorPythonScripting.set_keep_python_script_alive(True)
(ROOT/'Saved/Chapter01/editor-ready.json').write_text(json.dumps({'pid':os.getpid(),'engine':u.SystemLibrary.get_engine_version(),'toolset':'chapter01_tools.ChapterOneTools'}))
