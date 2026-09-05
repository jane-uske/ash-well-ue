"""Download a limited CC0 material set from the official Poly Haven API."""
import urllib.request,json,hashlib,pathlib,concurrent.futures,datetime,subprocess
ROOT=pathlib.Path(__file__).resolve().parent
HEADERS={'User-Agent':'AshWell local visual prototype asset download'}
def fetch(url):
 return urllib.request.urlopen(urllib.request.Request(url,headers=HEADERS),timeout=90).read()
materials=[];jobs=[]
for asset,short in [('slate_floor_03','WetStone'),('denim_fabric_06','DarkCloth'),('rusty_metal_04','OldSteel')]:
 info=json.loads(fetch('https://api.polyhaven.com/info/'+asset));files=json.loads(fetch('https://api.polyhaven.com/files/'+asset))
 mat={'id':asset,'name':info['name'],'material_name':short,'source_page':'https://polyhaven.com/a/'+asset,'license':'CC0-1.0','authors':info['authors'],'tile_size_m':[round(x/1000,6) for x in info['dimensions']],'textures':{}}
 channels=[('base_color','Diffuse','jpg',True),('roughness','Rough','jpg',False),('normal','nor_dx','png',False)]
 if asset=='slate_floor_03':channels.append(('displacement','Displacement','png',False))
 if asset=='rusty_metal_04' and 'arm' in files:channels.append(('arm','arm','jpg',False))
 for channel,key,ext,srgb in channels:
  f=files[key]['2k'][ext];rel='Textures/'+asset+'/'+f['url'].rsplit('/',1)[-1]
  rec={'path':rel,'category':channel,'source_page':mat['source_page'],'source_url':f['url'],'license':'CC0-1.0','resolution':[2048,2048],'srgb':srgb,'expected_size_bytes':f['size'],'source_md5':f['md5']}
  if channel=='normal':rec.update(normal_convention='DirectX',flip_green_channel=False)
  if channel=='arm':rec['channels']={'R':'ambient_occlusion','G':'roughness','B':'metallic'}
  mat['textures'][channel]=rec;jobs.append(rec)
 materials.append(mat)
print('Expected bytes',sum(x['expected_size_bytes'] for x in jobs),flush=True)
def download(rec):
 p=ROOT/rec['path'];p.parent.mkdir(parents=True,exist_ok=True)
 data=p.read_bytes() if p.exists() else fetch(rec['source_url'])
 assert len(data)==rec['expected_size_bytes'],(p,len(data));assert hashlib.md5(data).hexdigest()==rec['source_md5'].zfill(32),p
 assert data.startswith(b'\xff\xd8') or data.startswith(b'\x89PNG\r\n\x1a\n'),p
 p.write_bytes(data)
 check=subprocess.run(['sips','-g','pixelWidth','-g','pixelHeight',str(p)],capture_output=True,text=True,check=True).stdout
 assert 'pixelWidth: 2048' in check and 'pixelHeight: 2048' in check,(p,check)
 rec.update(size_bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),verified_dimensions=True)
 print('Verified',rec['path'],len(data),flush=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:list(pool.map(download,jobs))
manifest={'schema_version':1,'provider':'Poly Haven','license':'CC0-1.0','license_url':'https://polyhaven.com/license','api_credit':'Powered by Poly Haven','downloaded_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'path_base':'this manifest directory','materials':materials,'total_texture_bytes':sum(x['size_bytes'] for x in jobs),'validation':'API byte size and MD5 match; image signatures checked; decoded 2048x2048 with macOS sips.'}
(ROOT/'texture_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
print('COMPLETE',ROOT/'texture_manifest.json',flush=True)
