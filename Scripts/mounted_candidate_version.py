"""Hash the complete mounted candidate that a recording or human session uses."""
from pathlib import Path
import hashlib,subprocess,datetime,json
ROOT=Path(__file__).resolve().parents[1]
def snapshot():
    roots=[ROOT/'Content/AshWell/Combat/MountedChargeSample',ROOT/'Content/AshWell/MountedBoss/ReferenceProduction',ROOT/'Source/AshWell']
    paths={p for root in roots for p in root.rglob('*') if p.is_file()}
    paths.update([ROOT/'Content/AshWell/MountedBoss/L_MountedCourtyard.umap',ROOT/'Binaries/Mac/libUnrealEditor-AshWell.dylib'])
    hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}
    return {'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'branch':subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip(),'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'files_sha256':hashes,'candidate_sha256':hashlib.sha256(json.dumps(hashes,sort_keys=True).encode()).hexdigest()}
if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('output',type=Path);args=p.parse_args();args.output.write_text(json.dumps(snapshot(),indent=2)+'\n')
