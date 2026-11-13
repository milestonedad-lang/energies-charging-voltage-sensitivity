from pathlib import Path
import hashlib,json,zipfile,subprocess,sys
P=Path(__file__).resolve().parents[1];f=P/'source/交通电力_正式结果与复现包_v1.zip';target=P/'base_v1'
assert hashlib.sha256(f.read_bytes()).hexdigest()=='6c06e03fffd7d38041d10e2b8b3db4c4d71f17b6de0a26bac72c4513fc316cd4'
target.mkdir(parents=True,exist_ok=True)
with zipfile.ZipFile(f) as z:
 assert z.testzip() is None
 for name in z.namelist():assert (target/name).resolve().is_relative_to(target.resolve()),name
 for name,h in json.loads(z.read('SHA256SUMS.json')).items():assert hashlib.sha256(z.read(name)).hexdigest()==h,name
 z.extractall(target)
subprocess.run([sys.executable,str(target/'code/restore_inputs.py')],check=True)
print('Original v1 outputs, frozen inputs and pinned grid sources restored; original results not rerun.')
