from pathlib import Path
import unreal as u
ROOT=Path(__file__).resolve().parents[1]
s=ROOT/'Scripts/terrace_build.py'
# Complete the already generated, task-owned level without touching other maps.
exec(compile(s.read_text(),str(s),'exec'),{'__file__':str(s)})
