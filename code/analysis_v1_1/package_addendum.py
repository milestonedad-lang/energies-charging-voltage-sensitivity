from pathlib import Path
import io,os,json,hashlib,zipfile
P=Path(__file__).resolve().parents[1]
files=[P/'README.md',P/'source/交通电力_正式结果与复现包_v1.zip']
for sub in ['code','outputs','results','evidence']:
 for f in (P/sub).rglob('*'):
  if f.is_file() and '__pycache__' not in f.parts and f.suffix not in ['.zip','.tmp']:files.append(f)
m={str(f.relative_to(P)):hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(set(files))}
buf=io.BytesIO()
with zipfile.ZipFile(buf,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for name in m:z.writestr(name,(P/name).read_bytes())
 z.writestr('SHA256SUMS.json',json.dumps(m,ensure_ascii=False,indent=2))
f=P/'outputs/交通电力_等电量映射补充与复现包_v1_1.zip';tmp=f.with_suffix('.tmp')
with tmp.open('wb') as w:w.write(buf.getvalue());w.flush();os.fsync(w.fileno())
os.replace(tmp,f)
print(json.dumps({'file':str(f),'members':len(m),'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()},ensure_ascii=False))
