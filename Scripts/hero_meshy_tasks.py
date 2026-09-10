"""Compose the installed Meshy CLI using the user's explicitly supplied key file.
Never persist or print the key. Paid work requires user authorization in-session.
"""
from pathlib import Path
import os, sys, subprocess, json, re
R=Path(__file__).resolve().parents[1]
CLI=Path('/Users/rare/.codex/plugins/cache/openai-curated-remote/meshy-openai-plugin/0.4.1/skills/meshy-3d-generation/scripts/meshy_task.py')
O=R/'Saved/HeroComplete'
O.mkdir(parents=True,exist_ok=True)
raw=Path('/Users/rare/blender/.env').read_text().strip()
lines=[x.strip() for x in raw.splitlines() if x.strip() and not x.strip().startswith('#')]
key=next((x.split('=',1)[1].strip().strip('\"\'') for x in lines if re.match(r'^(?:export\s+)?MESHY_API_KEY\s*=',x)), '')
if not key and len(lines)==1 and '=' not in lines[0]:
    key=lines[0].strip('\"\'')
assert key, 'No credential in the explicitly authorized file'
env=os.environ.copy()
env['MESHY_API_KEY']=key
def run(*args):
    p=subprocess.run([sys.executable,str(CLI),*map(str,args)],cwd=R,env=env,text=True,capture_output=True)
    clean=(p.stdout+p.stderr).replace(key,'[REDACTED]').replace(key[:8]+'...','[REDACTED]')
    if p.returncode:
        raise RuntimeError(clean)
    return p.stdout.replace(key,'[REDACTED]'),clean
if __name__=='__main__':
    mode=sys.argv[1]
    if mode=='preflight':
        print(run('check-env')[1])
        out,clean=run('balance')
        (O/'balance-before.txt').write_text(clean)
        print(clean)
        print(run('get','--endpoint','/openapi/v1/animations','--task-id','library','--save',O/'library.json')[1])
    else:
        print(run(*sys.argv[1:])[1])
