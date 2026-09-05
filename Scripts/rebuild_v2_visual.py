"""Rebuild the detailed visual study from its versioned source assets."""
from pathlib import Path
root=Path(__file__).resolve().parents[1]
for filename in ['build_v2_materials.py','build_v2_scene.py','polish_v2.py','frame_v2_final.py','pier_v2_fill.py']:
    f=root/'Scripts'/filename
    exec(compile(f.read_text(),str(f),'exec'),{'__file__':str(f),'__name__':'__main__'})
