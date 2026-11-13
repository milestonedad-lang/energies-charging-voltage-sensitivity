from pathlib import Path
import sys,json,hashlib
import numpy as np,pandas as pd
P=Path(__file__).resolve().parents[1];base=P/'base_v1'
s=pd.read_csv(P/'results/new_scenarios.csv');pairs=pd.read_csv(P/'results/all_mapping_paired_comparisons.csv')
for r in s.itertuples():
 p=P/'results'/f'{r.feeder[:-2]}__mapping_{r.mapping_id:02}__{r.representation}.npz'
 with np.load(p,allow_pickle=False) as a:
  assert len(a['vmin'])==4344 and int(a['ok'].sum())==r.converged_hours
  assert np.isclose(a['vmin'].min(),r.min_voltage_pu,rtol=1e-12)
  assert np.isclose(a['loss_kW'].mean(),r.mean_loss_kW,rtol=1e-12)
for r in pairs.itertuples():
 prefix=f'{r.feeder[:-2]}__mapping_{r.mapping_id:02}__'
 with np.load(base/'results'/(prefix+'A.npz'),allow_pickle=False) as a, np.load((base if r.alternative=='B' else P)/'results'/(prefix+r.alternative+'.npz'),allow_pickle=False) as b:
  va=(a['vmin']<.95)|(a['vmax']>1.05);vb=(b['vmin']<.95)|(b['vmax']>1.05)
  assert int((va!=vb).sum())==r.disagreement_hours
  assert r.A_only_hours+r.alternative_only_hours+r.both_hours+r.neither_hours==4344
  assert r.A_only_hours+r.alternative_only_hours==r.disagreement_hours
old=pd.read_csv(base/'results/paired_comparisons.csv')
for r in pairs[pairs.alternative=='B'].itertuples():
 x=old[(old.feeder==r.feeder)&(old.setting==f'mapping_{r.mapping_id:02}')].iloc[0]
 assert r.A_only_hours==x.A_only_violating_hours and r.alternative_only_hours==x.alternative_only_violating_hours
manifest=json.loads((base/'SHA256SUMS.json').read_text())
for name,h in manifest.items():assert hashlib.sha256((base/name).read_bytes()).hexdigest()==h,name
out={'status':'PASS','new_arrays_checked':len(s),'paired_comparisons_checked':len(pairs),'all_reused_A_B_pairs_reproduce_v1':True,'all_140_original_bundle_members_unchanged':True}
(P/'evidence/saved_output_consistency_v1_1.json').write_text(json.dumps(out,indent=2));print(json.dumps(out))
