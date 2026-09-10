"""User-authorized Meshy action batch. Persist each ID before doing further work."""
from pathlib import Path
import json
from hero_meshy_tasks import run, R, O
RIG='01a08b53-5a67-7288-b94d-3b81566abc50'
actions=[('Idle',0),('Run',14),('Jump',13),('Dodge',158),('Slash',219),('Heavy',242),('CombatWalk',21)]
ledger=O/'motion-tasks.json'
tasks=json.loads(ledger.read_text()) if ledger.exists() else []
project=tasks[0]['project_dir'] if tasks else None
for name,action in actions:
    if any(t['name']==name for t in tasks):
        continue
    payload={'rig_task_id':RIG,'action_id':action}
    (O/f'payload-{name}.json').write_text(json.dumps(payload))
    out,_=run('create','--endpoint','/openapi/v1/animations','--payload-file',O/f'payload-{name}.json')
    task_id=out.strip()
    if not project:
        out,_=run('project-dir','--task-id',task_id,'--prompt','ashwell-hero-complete-motion')
        project=out.strip()
    item={'name':name,'action_id':action,'task_id':task_id,'project_dir':project,'rig_task_id':RIG}
    tasks.append(item)
    ledger.write_text(json.dumps(tasks,indent=2))
    run('record','--project-dir',project,'--task-id',task_id,'--task-type','animation','--stage','queued')
    print(json.dumps(item),flush=True)
