"""Read-only reuse of ArchitectureV2 FBX round-trip checks for these three files."""
from pathlib import Path
source=Path(__file__).resolve().parent.parent/'verify_architecture_v2.py'
code=source.read_text().replace('architecture_v2_manifest.json','foreground_manifest.json').replace('architecture_v2_verification.json','foreground_verification.json')
exec(compile(code,str(source),'exec'),globals())
