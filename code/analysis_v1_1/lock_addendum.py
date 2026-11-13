from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
P=Path(__file__).resolve().parents[1];B=P/'base_v1'
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
protocol={'version':'1.1','locked_at_UTC':datetime.now(timezone.utc).isoformat(),
 'status':'internal addendum locked before new voltage runs; v1 outcomes already known; not public preregistration',
 'reason':'v1 tested alternative mappings only for A/B; inspect whether the equal-energy comparisons depend on mapping 0',
 'parent_bundle_sha256':'6c06e03fffd7d38041d10e2b8b3db4c4d71f17b6de0a26bac72c4513fc316cd4',
 'parent_plan_sha256':sha(B/'source/protocol/outputs/研究方案锁定_v1.json'),
 'inputs_sha256':sha(B/'source/protocol/derived/paired_energy_inputs.npz'),
 'mappings_sha256':sha(B/'source/protocol/derived/zone_bus_mappings.csv'),
 'solver_sha256':sha(B/'code/power_flow.py'),
 'feeders':['case33bw.m','case69.m'],'mapping_ids':list(range(1,21)),
 'representations_new':['B-G','B-Z'],'reference':'A from unchanged verified v1 hourly outputs; original B retained for descriptive context',
 'energy_matching':'whole-record global and per-zone total matching, identical to v1; no measured truth',
 'main_settings':{'alpha':.25,'beta':.5,'EV_pf':1.,'slack_voltage_pu':1.,'lower_threshold_pu':.95,'upper_threshold_pu':1.05,'anchor_MW':126.91314},
 'new_scenario_count':80,'hours_per_scenario':4344,
 'validation_before_runs':'all new representation/mapping/feeder combinations at the corresponding representation aggregate input maximum hour; BFS versus independent AC nodal root; 80 cases; voltage difference <1e-7 and each residual <1e-8',
 'metrics':['paired hourly disagreement counts and rate; unresolved bounds','A-only, alternative-only, both, neither violation counts','signed and absolute hourly minimum-voltage difference','signed active-loss difference','full per-mapping results and conditional min/median/max; number of zero and nonzero mappings'],
 'postprocess':['lower thresholds 0.90,0.94,0.95; upper 1.05 unchanged','exclude the same 31 complete hours flagged by zero-status mismatch; no cell edits'],
 'reporting':'all 20 maps per feeder and representation; mapping 0 reported separately, never pooled as a 21st random map; do not select maps to favor a claim',
 'mapping_inference':'scenario envelope only; neither 20 independent empirical samples nor population probability; no p-values, no confidence interval across maps',
 'failures':'retain all failures; report disagreement lower/upper bounds; halt formal analysis if independent preflight gate fails',
 'claim_limits':['no causal attribution to 11-kW rule','no ranking of energy accuracy','no real Shenzhen grid claim','no claim of invariance over loading levels or power factors for energy-matched inputs'],
 'next':'decide bounded manuscript contribution from all new outcomes, including disappearance of disagreement'}
out=P/'evidence/analysis_addendum_v1_1.json'
assert not out.exists(),'Do not silently overwrite the locked addendum.'
out.write_text(json.dumps(protocol,ensure_ascii=False,indent=2))
print('Addendum locked:',sha(out))
