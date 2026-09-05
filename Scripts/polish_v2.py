from pathlib import Path
root=Path(__file__).resolve().parents[1]
for filename in ['tune_v2.py','add_v2_practicals.py']:
    f=root/'Scripts'/filename
    exec(compile(f.read_text(),str(f),'exec'),{'__file__':str(f),'__name__':'__main__'})
