"""Verify the deposited record without rerunning scientific calculations."""
from pathlib import Path
import io,json,hashlib,zipfile
import numpy as np

P=Path(__file__).resolve().parent
sha=lambda b:hashlib.sha256(b).hexdigest()
manifest=json.loads((P/'SHA256SUMS.json').read_text())
for n,v in manifest.items():
    f=(P/n).resolve()
    assert f.is_relative_to(P.resolve()),n
    raw=f.read_bytes()
    assert len(raw)==v['bytes'] and sha(raw)==v['sha256'],n

archives=0;arrays=0
def nested(raw):
    global archives,arrays
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        assert z.testzip() is None
        assert len(z.namelist())==len(set(z.namelist()))
        for n in z.namelist():
            assert not n.startswith('/') and '..' not in Path(n).parts,n
        if 'SHA256SUMS.json' in z.namelist():
            m=json.loads(z.read('SHA256SUMS.json'))
            for n,h in m.items():
                assert sha(z.read(n))==(h['sha256'] if isinstance(h,dict) else h),n
        archives+=1
        for n in z.namelist():
            if n.endswith('.zip'):nested(z.read(n))
            elif n.startswith('results/') and n.endswith('.npz'):
                with np.load(io.BytesIO(z.read(n)),allow_pickle=False) as d:
                    assert len(d['vmin'])==4344 and d['ok'].all(),n
                arrays+=1
nested((P/'analysis_archive/Traffic_Power_Analysis_v1_1.zip').read_bytes())
assert arrays==188
print(json.dumps({'status':'PASS','files_verified':len(manifest),'nested_archives_verified':archives,'scenario_arrays_verified':arrays,'hours_per_scenario':4344,'scientific_model_rerun':False}))
