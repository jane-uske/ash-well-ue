"""Regression for the AshWell Mac UE 5.8 editor shutdown crash. Close other project editors before running. Reimports existing battle assets through native MCP, then checks exit code and new crash directories."""
from pathlib import Path
import subprocess,time,json,os,sys
R=Path(__file__).resolve().parents[1];O=R/'Saved/EditorExit';C=Path.home()/'Library/Application Support/Epic/UnrealEngine/5.8/Saved/Crashes';results=[]
os.environ['DEVELOPER_DIR']='/Applications/Xcode-beta.app/Contents/Developer'
engine='/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor.app/Contents/MacOS/UnrealEditor'
def stage(s):
 args={'toolset_name':'Users.rare.dev.ash-well-ue.Scripts.chapter01_tools.ChapterOneTools','tool_name':'run_stage','arguments':{'stage':s}}
 env=dict(os.environ,NO_PROXY='127.0.0.1,localhost')
 with (O/f'mcp-{s}.log').open('w') as f:
  p=subprocess.run(['/Users/rare/.local/share/ashwell-mcp/venv/bin/python',str(R/'Scripts/chapter01_mcp.py'),'call_tool',json.dumps(args)],cwd=R,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=120)
  if p.returncode:raise RuntimeError('MCP stage failed: '+s)
for mode in (sys.argv[1:] or ['native','native_repeat','signal']):
 with (O/f'{mode}-stdout.log').open('w') as f:
  p=subprocess.Popen([engine,str(R/'AshWell.uproject'),'/Game/AshWell/Chapter01/L_Chapter01_Descent','-NoSplash',f'-ExecutePythonScript={R}/Scripts/chapter01_editor.py','-ModelContextProtocolStartServer','-ModelContextProtocolPort=19854',f'-abslog={O}/{mode}.log'],cwd=R,stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
  ready=R/'Saved/Chapter01/editor-ready.json';until=time.monotonic()+90
  while time.monotonic()<until and p.poll() is None:
   try:
    if json.loads(ready.read_text())['pid']==p.pid:break
   except (FileNotFoundError,ValueError):pass
   time.sleep(.5)
  else:
   p.kill();p.wait();raise RuntimeError('Editor startup failed')
  stage('battleassets');time.sleep(2)
  if mode=='signal':p.terminate()
  else:stage('shutdown')
  try:code=p.wait(timeout=55)
  except subprocess.TimeoutExpired:p.kill();p.wait();code='timeout'
  time.sleep(2)
  log=(O/f'{mode}.log').read_text(errors='replace');crashes=[q.name for q in C.iterdir() if f'pid-{p.pid}-' in q.name]
  d={'mode':mode,'pid':p.pid,'exit_code':code,'cleanup_hook':'AW_EDITOR_EXIT late callback drain' in (O/f'{mode}-stdout.log').read_text(errors='replace'),'normal_exit':'LogExit: Exiting.' in log,'new_reports':crashes};d['passed']=code==0 and d['cleanup_hook'] and (d['normal_exit'] if mode!='signal' else 'Mac GracefulTerminationHandler' in log) and not crashes;results.append(d);print(json.dumps(d),flush=True)
  (R/'Docs/Verification/EditorExit/after.json').write_text(json.dumps(results,indent=2))
  if not d['passed']:break
