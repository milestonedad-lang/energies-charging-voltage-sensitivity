from pathlib import Path
import hashlib,json,zipfile,io,os
P=Path(__file__).resolve().parents[1]
files=[P/'README.md',P/'source/Protocol_v1.zip']
for sub in ['code','results','figures','outputs','evidence']:
 for f in (P/sub).rglob('*'):
  if not f.is_file() or '__pycache__' in f.parts:continue
  if f.suffix=='.zip' or f.name.endswith('.alignment.svg') or f.name in ['figure_alignment.svg','figure_collision_overlay.pdf']:continue
  files.append(f)
manifest={str(f.relative_to(P)):hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(set(files))}
mem=io.BytesIO()
with zipfile.ZipFile(mem,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for name in manifest:z.writestr(name,(P/name).read_bytes())
 z.writestr('SHA256SUMS.json',json.dumps(manifest,ensure_ascii=False,indent=2))
out=P/'outputs/交通电力_正式结果与复现包_v1.zip';tmp=out.with_suffix('.tmp')
with tmp.open('wb') as f:f.write(mem.getvalue());f.flush();os.fsync(f.fileno())
os.replace(tmp,out)
print(json.dumps({'file':str(out),'bytes':out.stat().st_size,'members':len(manifest),'sha256':hashlib.sha256(out.read_bytes()).hexdigest()},ensure_ascii=False))
