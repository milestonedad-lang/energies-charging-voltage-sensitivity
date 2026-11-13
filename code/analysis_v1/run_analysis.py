from pathlib import Path
import os,json,hashlib,time,sys
import numpy as np,pandas as pd,scipy
from power_flow import load_case,bfs,ac_nodal_root,make_loads

P=Path(__file__).resolve().parents[1];Q=P/'source/protocol'
plan_file=Q/'outputs/研究方案锁定_v1.json'
assert hashlib.sha256(plan_file.read_bytes()).hexdigest()=='e65af2bc8a2a8d0b4210d12f3d701eb9335281695987c2100766a85c6bf1f0a2'
plan=json.loads(plan_file.read_text());T=4344
data=np.load(Q/'derived/paired_energy_inputs.npz',allow_pickle=False)
A=data['A_kWh'];B=data['B_kWh'];zones=data['zone_ids'];timestamps=data['timestamps']
assert A.shape==B.shape==(T,275) and (A.sum(0)>0).all() and (B.sum(0)>0).all()
representations={'A':A,'B':B,'B-G':B*(A.sum()/B.sum()),'B-Z':B*(A.sum(0)/B.sum(0))}
assert np.isclose(representations['B-G'].sum(),A.sum(),rtol=1e-12)
assert np.allclose(representations['B-Z'].sum(0),A.sum(0),rtol=1e-12)
anchor=float(np.quantile(A.sum(1)/1000,.99,method='linear'));assert np.isclose(anchor,126.91314)
maps=pd.read_csv(Q/'derived/zone_bus_mappings.csv')
grids=json.loads((Q/'evidence/grid_sources.json').read_text())
cases={}
for r in grids['files']:
    f=Q/'source'/r['file'];assert hashlib.sha256(f.read_bytes()).hexdigest()==r['sha256']
    cases[r['file']]=load_case(f)
def mapping(case_id,mapid):
    frame=maps[(maps.feeder==case_id)&(maps.mapping_id==mapid)].set_index('TAZID')
    return frame.loc[zones].bus_id.to_numpy()

# These implementation details are written before calculating any validation or outcome voltage.
validation_hours=sorted(set([0]+[int(np.argmax(E.sum(1))) for E in representations.values()]))
setup={'date':'2026-11-06','protocol_sha256':hashlib.sha256(plan_file.read_bytes()).hexdigest(),
 'validation_hour_indices_input_selected':validation_hours,
 'validation_cases':'both backgrounds beta=0.5 and 1; all 4 representations at selected input hours under main settings; A and B at maximum aggregate A, alpha=.5 beta=.6 pf=.95',
 'BFS_tolerance':1e-12,'BFS_max_iterations':200,
 'root':'SciPy hybr, rectangular AC power-balance equations, independent flat start, xtol=1e-11 maxfev=5000',
 'versions':{'python':sys.version.split()[0],'numpy':np.__version__,'pandas':pd.__version__,'scipy':scipy.__version__},
 'source_case_files_sha256':{r['file']:r['sha256'] for r in grids['files']},
 'code_sha256':{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in (P/'code').glob('*.py')}}
(P/'evidence/implementation_setup_before_voltage.json').write_text(json.dumps(setup,indent=2))

validation=[];baselines=[]
for cid,case in cases.items():
    scenarios=[]
    for beta in [.5,1.]:
        scenarios.append((f'background_beta_{beta}',-1,make_loads(case,np.zeros((1,275)),mapping(cid,0),anchor,alpha=0,beta=beta)[0]))
    for hour in validation_hours:
        for name,E in representations.items():
            scenarios.append((f'main_{name}',hour,make_loads(case,E[hour],mapping(cid,0),anchor)[0]))
    hour=int(np.argmax(A.sum(1)))
    for name in ['A','B']:
        scenarios.append((f'stress_{name}',hour,make_loads(case,representations[name][hour],mapping(cid,0),anchor,.5,.6,.95)[0]))
    for label,hour,loads in scenarios:
        result=bfs(case,loads);Vroot,res,sol=ac_nodal_root(case,loads)
        diff=float(np.max(np.abs(result['V'][0]-Vroot)))
        validation.append({'feeder':cid,'case':label,'hour_index':hour,
          'BFS_ok':bool(result['ok'][0]),'root_solver_success':bool(sol.success),
          'root_nfev':int(sol.nfev),'root_message':str(sol.message),
          'max_complex_voltage_difference_pu':diff,'max_magnitude_difference_pu':float(np.max(np.abs(result['vm'][0]-np.abs(Vroot)))),
          'BFS_residual_pu':float(result['residual_pu'][0]),'root_residual_pu':res,
          'BFS_balance_error_kW':float(result['balance_error_kW'][0]),
          'BFS_vmin_pu':float(result['vmin'][0]),'BFS_loss_kW':float(result['loss_kW'][0]),
          'input_load_sha256':hashlib.sha256(np.ascontiguousarray(loads).tobytes()).hexdigest(),
          'pass':bool(result['ok'][0] and diff<1e-7 and res<1e-8)})
        if label.startswith('background'):
            baselines.append({'feeder':cid,'beta':float(label.split('_')[-1]),
              'load_P_MW':float(loads.real.sum()),'load_Q_Mvar':float(loads.imag.sum()),
              'vmin_pu':float(result['vmin'][0]),'loss_kW':float(result['loss_kW'][0]),
              'violates_study_0p95':bool(result['vmin'][0]<.95),'converged':bool(result['ok'][0])})
pd.DataFrame(validation).to_csv(P/'evidence/independent_solver_validation.csv',index=False)
pd.DataFrame(baselines).to_csv(P/'results/no_EV_baselines.csv',index=False)
gate={'status':'PASS' if all(r['pass'] for r in validation) else 'FAIL',
 'validation_case_count':len(validation),'max_complex_voltage_difference_pu':max(r['max_complex_voltage_difference_pu'] for r in validation),
 'max_root_residual_pu':max(r['root_residual_pu'] for r in validation),
 'max_BFS_residual_pu':max(r['BFS_residual_pu'] for r in validation),
 'max_abs_balance_error_kW':max(abs(r['BFS_balance_error_kW']) for r in validation)}
(P/'evidence/validation_gate.json').write_text(json.dumps(gate,indent=2));print('GATE',json.dumps(gate),flush=True)
assert gate['status']=='PASS','Validation failed; formal outcomes were not run.'

settings=[('main',.25,.5,1.,0),('alpha_010',.1,.5,1.,0),('alpha_050',.5,.5,1.,0),
          ('beta_040',.25,.4,1.,0),('beta_060',.25,.6,1.,0),('pf_095',.25,.5,.95,0)]
settings += [(f'mapping_{j:02}',.25,.5,1.,j) for j in range(1,21)]
summaries=[];paired=[];main_outputs={};solved_hours=0;start=time.time()
def compare(case_id,setting,ref,alt,lo=.95,mask=None):
    if mask is None:mask=np.ones(T,bool)
    ok=ref['ok']&alt['ok']&mask;unknown=int((mask&~ok).sum());den=int(mask.sum())
    va=((ref['vmin']<lo)|(ref['vmax']>1.05))&ok
    vb=((alt['vmin']<lo)|(alt['vmax']>1.05))&ok
    disagree=(va!=vb)&ok;n=int(disagree.sum())
    return {'feeder':case_id,'setting':setting,'lower_threshold':lo,'n_hours':den,'n_valid_pairs':int(ok.sum()),'unresolved_pairs':unknown,
      'A_only_violating_hours':int((va&~vb).sum()),'alternative_only_violating_hours':int((vb&~va).sum()),
      'both_violating_hours':int((va&vb).sum()),'neither_violating_hours':int((ok&~va&~vb).sum()),
      'disagreement_rate_lower':n/den,'disagreement_rate_upper':(n+unknown)/den,
      'A_minus_alternative_violation_rate_pp':100*(int(va.sum())-int(vb.sum()))/den if unknown==0 else np.nan,
      'mean_alternative_minus_A_vmin_pu':float(np.mean(alt['vmin'][ok]-ref['vmin'][ok])),
      'mean_alternative_minus_A_loss_kW':float(np.mean(alt['loss_kW'][ok]-ref['loss_kW'][ok]))}

for cid,case in cases.items():
    for setting,alpha,beta,pf,mapid in settings:
        results={};reps=list(representations) if setting=='main' else ['A','B']
        for name in reps:
            loads=make_loads(case,representations[name],mapping(cid,mapid),anchor,alpha,beta,pf)
            out=bfs(case,loads);solved_hours+=T;results[name]=out
            record={'feeder':cid,'setting':setting,'representation':name,'alpha':alpha,'beta':beta,'pf':pf,'mapping_id':mapid,
              'n_hours':T,'converged_hours':int(out['ok'].sum()),'unresolved_hours':int((~out['ok']).sum()),
              'voltage_violating_hours':int((((out['vmin']<.95)|(out['vmax']>1.05))&out['ok']).sum()),
              'minimum_voltage_pu':float(out['vmin'][out['ok']].min()),'mean_minimum_voltage_pu':float(out['vmin'][out['ok']].mean()),
              'mean_loss_kW':float(out['loss_kW'][out['ok']].mean()),
              'max_residual_pu':float(out['residual_pu'].max()),'max_abs_balance_error_kW':float(np.abs(out['balance_error_kW']).max()),
              'max_iterations':int(out['iterations'].max()),'common_scale':float(alpha*case['p'].sum()/anchor)}
            record['violating_hour_fraction_lower']=record['voltage_violating_hours']/T
            record['violating_hour_fraction_upper']=(record['voltage_violating_hours']+record['unresolved_hours'])/T
            summaries.append(record)
            saved={k:out[k] for k in ['vmin','vmax','loss_kW','residual_pu','ok','iterations','balance_error_kW']}
            if setting=='main':saved['voltage_magnitude_pu']=out['vm']
            np.savez_compressed(P/'results'/f'{cid[:-2]}__{setting}__{name}.npz',**saved)
        for name in reps[1:]:
            row=compare(cid,setting,results['A'],results[name]);row['alternative']=name;paired.append(row)
        if setting=='main':main_outputs[cid]=results
        pd.DataFrame(summaries).to_csv(P/'results/all_scenarios.csv',index=False)
        pd.DataFrame(paired).to_csv(P/'results/paired_comparisons.csv',index=False)
        print(cid,setting,'hours',solved_hours,'seconds',round(time.time()-start,2),flush=True)

post=[];flags=pd.read_csv(Q/'derived/hour_quality_flags.csv').zero_status_mismatch_any_zone.to_numpy(bool)
for cid,results in main_outputs.items():
    for name in ['B','B-G','B-Z']:
        for lower in [.90,.94,.95]:
            row=compare(cid,'threshold_check',results['A'],results[name],lo=lower);row['alternative']=name;post.append(row)
        row=compare(cid,'exclude_31_flagged_hours',results['A'],results[name],mask=~flags);row['alternative']=name;post.append(row)
pd.DataFrame(post).to_csv(P/'results/threshold_and_pairing_sensitivity.csv',index=False)

# Paired seven-day moving blocks, shared across all primary contrasts and feeders.
rng=np.random.default_rng(20261106)
starts=rng.integers(0,181-7+1,size=(2000,int(np.ceil(181/7))))
idx=(starts[:,:,None]+np.arange(7)[None,None,:]).reshape(2000,-1)[:,:181]
boot=[]
for cid,results in main_outputs.items():
    ref=results['A']
    for name in ['B','B-G','B-Z']:
        alt=results[name]
        if not (ref['ok']&alt['ok']).all():continue
        ra=(ref['vmin']<.95)|(ref['vmax']>1.05);rb=(alt['vmin']<.95)|(alt['vmax']>1.05)
        values={'disagreement_rate':(ra!=rb).astype(float),
         'A_minus_alternative_violation_rate_pp':100*(ra.astype(float)-rb.astype(float)),
         'alternative_minus_A_vmin_pu':alt['vmin']-ref['vmin'],
         'alternative_minus_A_loss_kW':alt['loss_kW']-ref['loss_kW']}
        for metric,v in values.items():
            daily=v.reshape(181,24).mean(1);sample=daily[idx].mean(1)
            low,high=np.quantile(sample,[.025,.975])
            boot.append({'feeder':cid,'alternative':name,'metric':metric,'estimate':float(v.mean()),
              'temporal_resampling_percentile_2p5':float(low),'temporal_resampling_percentile_97p5':float(high),
              'draws':2000,'block_days':7,'seed':20261106})
pd.DataFrame(boot).to_csv(P/'results/conditional_temporal_resampling.csv',index=False)
main=pd.DataFrame(summaries).query("setting == 'main'")
main.to_csv(P/'outputs/四组主对照结果.csv',index=False)
pd.DataFrame(paired).query("setting == 'main'").to_csv(P/'outputs/主对照配对差异.csv',index=False)
summary={'status':'COMPLETE','protocol_unchanged':hashlib.sha256(plan_file.read_bytes()).hexdigest()==setup['protocol_sha256'],
 'validation':gate,'scenario_count':len(summaries),'scenario_hours':solved_hours,
 'main_scenario_hours':int(len(main)*T),'nonconverged_scenario_hours':sum(r['unresolved_hours'] for r in summaries),
 'maximum_nodal_residual_pu':max(r['max_residual_pu'] for r in summaries),
 'maximum_abs_balance_error_kW':max(r['max_abs_balance_error_kW'] for r in summaries),
 'elapsed_formal_seconds':time.time()-start,'outcome_selection_or_parameter_changes':False}
(P/'evidence/execution_summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2),flush=True)
