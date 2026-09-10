"""Collect the existing authorized task ledger; never creates new jobs."""
from pathlib import Path
import json
from hero_meshy_tasks import run, R, O
tasks=json.loads((O/'motion-tasks.json').read_text())
for t in tasks:
    d=Path(t['project_dir'])
    taskfile=d/f"task_{t['task_id']}.json"
    if not taskfile.exists():
        print(run('poll','--endpoint','/openapi/v1/animations','--task-id',t['task_id'],'--timeout',600,'--project-dir',d)[1],flush=True)
    task=json.loads(taskfile.read_text())
    assert task['status']=='SUCCEEDED'
    target=d/(t['name']+'.glb')
    if not target.exists():
        print(run('download','--url',task['result']['animation_glb_url'],'--output',target)[1],flush=True)
    run('record','--project-dir',d,'--task-id',t['task_id'],'--task-type','animation','--stage','downloaded','--files',target.name)
    t['file']=str(target)
    t['consumed_credits']=task.get('consumed_credits')
    (O/'motion-tasks.json').write_text(json.dumps(tasks,indent=2))
    print(json.dumps({'name':t['name'],'file':str(target),'credits':t['consumed_credits']}),flush=True)
out,clean=run('balance')
(O/'balance-after-motions.txt').write_text(clean)
print(clean)
