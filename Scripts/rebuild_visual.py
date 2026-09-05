"""Reimport changed source meshes, rebuild the map, and apply the visual grade."""
import pathlib
scripts = pathlib.Path(__file__).resolve().parent
for name in ['build_scene.py', 'retune_scene.py']:
    path = scripts / name
    exec(compile(path.read_text(), str(path), 'exec'), {'__file__': str(path), '__name__': '__main__'})
