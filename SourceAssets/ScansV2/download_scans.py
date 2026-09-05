"""Fetch attributed CC0 photogrammetry source assets from Poly Haven."""
import concurrent.futures, hashlib, json, pathlib, urllib.request
ROOT = pathlib.Path(__file__).resolve().parent
ROOT.mkdir(parents=True, exist_ok=True)
headers = {'User-Agent': 'AshWell-visual-study/1.0'}
manifest = {'license': 'CC0', 'license_url': 'https://polyhaven.com/license', 'assets': []}
jobs = []
for asset in ['rock_face_01', 'boulder_01']:
    data = json.load(urllib.request.urlopen(urllib.request.Request('https://api.polyhaven.com/files/' + asset, headers=headers), timeout=40))
    info = json.load(urllib.request.urlopen(urllib.request.Request('https://api.polyhaven.com/info/' + asset, headers=headers), timeout=40))
    entry = {'id': asset, 'source': 'https://polyhaven.com/a/' + asset, 'author': info.get('authors'), 'textures': {}}
    for channel, remote, fmt in [('mesh', 'fbx', 'fbx'), ('base_color', 'Diffuse', 'jpg'), ('roughness', 'Rough', 'jpg'), ('normal', 'nor_dx', 'png')]:
        item = data[remote]['4k'][fmt]
        rel = asset + '/' + item['url'].rsplit('/', 1)[1]
        spec = {'path': rel, 'url': item['url'], 'md5': item['md5'], 'size': item['size']}
        if channel == 'mesh': entry['mesh'] = spec
        else: entry['textures'][channel] = spec
        jobs.append(spec)
    manifest['assets'].append(entry)

def download(spec):
    dest = ROOT / spec['path']; dest.parent.mkdir(parents=True, exist_ok=True)
    if not dest.exists() or dest.stat().st_size != spec['size']:
        with urllib.request.urlopen(urllib.request.Request(spec['url'], headers=headers), timeout=120) as response:
            raw = response.read()
        assert hashlib.md5(raw).hexdigest() == spec['md5'], spec['path']
        dest.write_bytes(raw)
    raw = dest.read_bytes()
    assert hashlib.md5(raw).hexdigest() == spec['md5'], spec['path']
    spec['sha256'] = hashlib.sha256(raw).hexdigest()
    print('Verified', spec['path'], len(raw), flush=True)

with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
    list(pool.map(download, jobs))
(ROOT / 'manifest.json').write_text(json.dumps(manifest, indent=2))
print('SCAN ASSETS READY', flush=True)
