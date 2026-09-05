from pathlib import Path
root=Path(__file__).resolve().parents[1]
for filename in ['verify_v2.py','capture_v2.py']:
    f=root/'Scripts'/filename
    exec(compile(f.read_text(),str(f),'exec'),{'__file__':str(f),'__name__':'__main__'})
