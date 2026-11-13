"""Restore frozen input bundle and fetch only the two hash-pinned grid data files."""
from pathlib import Path
import hashlib,json,zipfile,urllib.request
P=Path(__file__).resolve().parents[1]
f=P/'source/Protocol_v1.zip';target=P/'source/protocol'
assert hashlib.sha256(f.read_bytes()).hexdigest()=='c2e540d9d3baf1c0125969c3c16d3880e9a4b5ad4a76849a80fc935d8c5457b1'
target.mkdir(parents=True,exist_ok=True)
with zipfile.ZipFile(f) as z:
 assert z.testzip() is None
 for name in z.namelist():
  assert (target/name).resolve().is_relative_to(target.resolve()),name
 manifest=json.loads(z.read('SHA256SUMS.json'))
 for name,h in manifest.items():assert hashlib.sha256(z.read(name)).hexdigest()==h,name
 z.extractall(target)
for r in json.loads((target/'evidence/grid_sources.json').read_text())['files']:
 out=target/'source'/r['file']
 if out.exists() and hashlib.sha256(out.read_bytes()).hexdigest()==r['sha256']:continue
 with urllib.request.urlopen(r['url'],timeout=60) as res:raw=res.read()
 assert hashlib.sha256(raw).hexdigest()==r['sha256'],r['file']
 out.write_bytes(raw)
print('Frozen protocol inputs restored; both grid source hashes verified.')
