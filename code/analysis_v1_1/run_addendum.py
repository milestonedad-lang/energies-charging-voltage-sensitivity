from pathlib import Path
import sys,json,hashlib,time
from datetime import datetime,timezone
import numpy as np,pandas as pd,scipy
P=Path(__file__).resolve().parents[1];B=P/'base_v1';Q=B/'source/protocol'
sys.path.insert(0,str(B/'code'))
from power_flow import load_case,bfs,ac_nodal_root,make_loads
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
f=P/'evidence/analysis_addendum_v1_1.json'
assert sha(f)=='6bf8b62655528b2c58b0d2842edcafcc37321477410ef2f59c67df64a4c50868'
plan=json.loads(f.read_text())
for file,key in [(Q/'outputs/研究方案锁定_v1.json','parent_plan_sha256'),(Q/'derived/paired_energy_inputs.npz','inputs_sha256'),(Q/'derived/zone_bus_mappings.csv','mappings_sha256'),(B/'code/power_flow.py','solver_sha256')]:assert sha(file)==plan[key]
original=json.loads((B/'SHA256SUMS.json').read_text())
for name,h in original.items():
 if name.startswith('results/') or name=='code/power_flow.py':assert sha(B/name)==h,name
raw=np.load(Q/'derived/paired_energy_inputs.npz',allow_pickle=False)
A,Bin,zones=raw['A_kWh'],raw['B_kWh'],raw['zone_ids'];T=len(A)
assert A.shape==Bin.shape==(4344,275)
E={'B-G':Bin*A.sum()/Bin.sum(),'B-Z':Bin*(A.sum(0)/Bin.sum(0))}
assert np.isclose(E['B-G'].sum(),A.sum(),rtol=1e-12)
assert np.allclose(E['B-Z'].sum(0),A.sum(0),rtol=1e-12)
anchor=float(np.quantile(A.sum(1)/1000,.99,method='linear'));assert np.isclose(anchor,plan['main_settings']['anchor_MW'])
maps=pd.read_csv(Q/'derived/zone_bus_mappings.csv');grids=json.loads((Q/'evidence/grid_sources.json').read_text())
cases={}
for r in grids['files']:
 assert sha(Q/'source'/r['file'])==r['sha256'];cases[r['file']]=load_case(Q/'source'/r['file'])
def mapping(cid,i):return maps[(maps.feeder==cid)&(maps.mapping_id==i)].set_index('TAZID').loc[zones].bus_id.to_numpy()
flags=pd.read_csv(Q/'derived/hour_quality_flags.csv').zero_status_mismatch_any_zone.to_numpy(bool);assert flags.sum()==31
setup={'started_at_UTC':datetime.now(timezone.utc).isoformat(),'addendum_sha256':sha(f),'run_code_sha256':sha(Path(__file__)),'solver_sha256':sha(B/'code/power_flow.py'),'versions':{'python':sys.version.split()[0],'numpy':np.__version__,'pandas':pd.__version__,'scipy':scipy.__version__},'input_selected_validation_hours':{k:int(np.argmax(v.sum(1))) for k,v in E.items()},'reused_v1_hourly_scenarios':80,'v1_saved_outputs_sha256_verified':True}
(P/'evidence/setup_before_new_voltage.json').write_text(json.dumps(setup,indent=2))
validation=[]
for cid,case in cases.items():
 for mid in plan['mapping_ids']:
  for name,energy in E.items():
   hour=setup['input_selected_validation_hours'][name]
   loads=make_loads(case,energy[hour],mapping(cid,mid),anchor)
   a=bfs(case,loads);v,res,sol=ac_nodal_root(case,loads[0]);diff=float(np.abs(a['V'][0]-v).max())
   validation.append({'feeder':cid,'mapping_id':mid,'representation':name,'hour_index':hour,'BFS_ok':bool(a['ok'][0]),'root_success':bool(sol.success),'complex_voltage_difference_pu':diff,'root_residual_pu':res,'BFS_residual_pu':float(a['residual_pu'][0]),'pass':bool(a['ok'][0] and sol.success and diff<1e-7 and res<1e-8)})
pd.DataFrame(validation).to_csv(P/'evidence/new_independent_validation.csv',index=False)
gate={'status':'PASS' if all(r['pass'] for r in validation) else 'FAIL','cases':len(validation),'max_complex_voltage_difference_pu':max(r['complex_voltage_difference_pu'] for r in validation),'max_root_residual_pu':max(r['root_residual_pu'] for r in validation)}
(P/'evidence/new_validation_gate.json').write_text(json.dumps(gate,indent=2));print('GATE',gate,flush=True)
assert gate['status']=='PASS','Do not run formal supplementary outcomes after a failed gate.'
def saved(cid,mid,name):
 f=B/'results'/f'{cid[:-2]}__mapping_{mid:02}__{name}.npz'
 with np.load(f,allow_pickle=False) as r:return {k:r[k].copy() for k in r.files}
def compare(cid,mid,name,ref,alt,lo=.95,mask=None):
 if mask is None:mask=np.ones(T,bool)
 ok=ref['ok']&alt['ok']&mask;den=int(mask.sum());u=int((mask&~ok).sum())
 va=((ref['vmin']<lo)|(ref['vmax']>1.05))&ok;vb=((alt['vmin']<lo)|(alt['vmax']>1.05))&ok
 n=int(((va!=vb)&ok).sum());delta=alt['vmin'][ok]-ref['vmin'][ok]
 return {'feeder':cid,'mapping_id':mid,'alternative':name,'lower_threshold':lo,'hours':den,'valid_pairs':int(ok.sum()),'unresolved_pairs':u,'A_only_hours':int((va&~vb).sum()),'alternative_only_hours':int((vb&~va).sum()),'both_hours':int((va&vb).sum()),'neither_hours':int((ok&~va&~vb).sum()),'disagreement_hours':n,'disagreement_rate_lower':n/den,'disagreement_rate_upper':(n+u)/den,'A_violating_fraction':int(va.sum())/den,'alternative_violating_fraction':int(vb.sum())/den,'mean_alt_minus_A_vmin_pu':float(delta.mean()),'mean_absolute_vmin_difference_pu':float(np.abs(delta).mean()),'max_absolute_vmin_difference_pu':float(np.abs(delta).max()),'mean_alt_minus_A_loss_kW':float((alt['loss_kW'][ok]-ref['loss_kW'][ok]).mean())}
rows=[];sens=[];scenarios=[];start=time.time()
for cid,case in cases.items():
 for mid in plan['mapping_ids']:
  ref=saved(cid,mid,'A');alts={'B':saved(cid,mid,'B')}
  for name,energy in E.items():
   out=bfs(case,make_loads(case,energy,mapping(cid,mid),anchor))
   keep={k:out[k] for k in ['vmin','vmax','loss_kW','residual_pu','ok','iterations','balance_error_kW']}
   np.savez_compressed(P/'results'/f'{cid[:-2]}__mapping_{mid:02}__{name}.npz',**keep);alts[name]=keep
   scenarios.append({'feeder':cid,'mapping_id':mid,'representation':name,'hours':T,'converged_hours':int(out['ok'].sum()),'unresolved_hours':int((~out['ok']).sum()),'max_residual_pu':float(out['residual_pu'].max()),'max_abs_balance_error_kW':float(np.abs(out['balance_error_kW']).max()),'min_voltage_pu':float(out['vmin'][out['ok']].min()),'mean_vmin_pu':float(out['vmin'][out['ok']].mean()),'mean_loss_kW':float(out['loss_kW'][out['ok']].mean())})
  for name,alt in alts.items():
   rows.append(compare(cid,mid,name,ref,alt))
   if name!='B':
    for lo in [.90,.94,.95]:sens.append({'sensitivity':'threshold',**compare(cid,mid,name,ref,alt,lo)})
    sens.append({'sensitivity':'exclude_31_flagged_hours',**compare(cid,mid,name,ref,alt,.95,~flags)})
 print(cid,'complete',len(scenarios),'new scenarios',flush=True)
pd.DataFrame(rows).to_csv(P/'results/all_mapping_paired_comparisons.csv',index=False)
pd.DataFrame(scenarios).to_csv(P/'results/new_scenarios.csv',index=False)
pd.DataFrame(sens).to_csv(P/'results/threshold_and_flag_sensitivity.csv',index=False)
# Preserve mapping 0 as a separate fixed comparator, never a 21st random mapping.
old=pd.read_csv(B/'results/paired_comparisons.csv');old=old[old.setting=='main'];old.to_csv(P/'results/fixed_mapping_0_reference.csv',index=False)
summary=[]
for (cid,name),g in pd.DataFrame(rows).groupby(['feeder','alternative']):
 v=g.disagreement_rate_lower
 summary.append({'feeder':cid,'alternative':name,'mapping_count':len(g),'nonzero_mapping_count':int((g.disagreement_hours>0).sum()),'zero_mapping_count':int((g.disagreement_hours==0).sum()),'minimum_disagreement_rate':float(v.min()),'median_disagreement_rate':float(v.median()),'maximum_disagreement_rate':float(v.max()),'median_mean_absolute_vmin_difference_pu':float(g.mean_absolute_vmin_difference_pu.median()),'maximum_unresolved_pairs':int(g.unresolved_pairs.max())})
pd.DataFrame(summary).to_csv(P/'outputs/映射敏感性汇总_v1_1.csv',index=False)
final={'status':'COMPLETE','new_scenario_count':len(scenarios),'new_scenario_hours':len(scenarios)*T,'reused_A_B_scenario_hours':80*T,'combined_four_representation_mapping_scenario_hours':160*T,'nonconverged_new_scenario_hours':sum(r['unresolved_hours'] for r in scenarios),'validation_gate':gate,'maximum_new_residual_pu':max(r['max_residual_pu'] for r in scenarios),'maximum_new_abs_balance_error_kW':max(r['max_abs_balance_error_kW'] for r in scenarios),'addendum_unchanged':sha(f)==setup['addendum_sha256'],'parent_solver_unchanged':sha(B/'code/power_flow.py')==setup['solver_sha256'],'elapsed_formal_seconds':time.time()-start,'settings_changed_after_outcomes':False,'added_analysis_not_original_primary':True}
(P/'evidence/execution_summary_v1_1.json').write_text(json.dumps(final,indent=2));print(json.dumps(final,indent=2),flush=True)
