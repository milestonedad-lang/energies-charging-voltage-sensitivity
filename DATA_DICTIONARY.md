# Data dictionary and analysis boundaries

## Direct input access: source_data/

`paired_energy_inputs.npz` is read with `numpy.load(..., allow_pickle=False)`.

| Key | Shape | Meaning / unit |
| --- | --- | --- |
| A_kWh | 4344 × 275 | Released estimated hourly zone energy from UrbanEV volume.csv; kWh |
| B_kWh | 4344 × 275 | Released estimated hourly zone energy from volume-11kW.csv; kWh |
| timestamps | 4344 | Source local clock strings, 2022-09-01 00:00:00 through 2023-02-28 23:00:00; no timezone conversion |
| zone_ids | 275 | UrbanEV traffic-analysis-zone identifiers, aligned with energy columns |
| static_piles | 275 | Static pile count per zone in analyzed release |
| static_station_counts | 275 | Static station count per zone in analyzed release |

`zone_bus_mappings.csv`: columns feeder, mapping_id, TAZID, bus_id; 11,550 rows. Two feeders × 21 mappings × 275 zones. Mapping 0 is fixed, and mappings 1–20 are synthetic alternatives. They are not city network connections.

`hour_quality_flags.csv`: one row per hour, fields time and zero_status_mismatch_any_zone. True means at least one zone differs between zero and nonzero energy status in A versus B. Exactly 31 complete hours are flagged. This is not a missing-value mask.

`数据字典_v1.csv`, `grid_sources.json`, and `paired_input_checks.json` preserve the earlier detailed dictionary, pinned case-file URLs/SHA-256 values, and input audit.

## Hourly results inside analysis_archive/Traffic_Power_Analysis_v1_1.zip

The top-level analysis `results/` contains 80 new energy-matched mapping arrays. The nested original v1 archive contains 108 original arrays. Each represents 4,344 hours; there are 188 distinct scenarios and 816,672 scenario-hours. Do not double-count reused A/B arrays.

| NPZ key | Meaning / unit |
| --- | --- |
| vmin, vmax | Hourly minimum and maximum voltage magnitude among non-slack buses; p.u. |
| loss_kW | Hourly active branch losses; kW |
| residual_pu | Maximum non-slack complex-power-balance residual; p.u. |
| ok | Boolean numerical acceptance flag |
| iterations | Solver iteration count |
| balance_error_kW | Slack active injection minus demand and losses; kW |
| voltage_magnitude_pu | Bus voltage magnitudes; included for original main scenarios only |

CSV paired decisions retain A-only, alternative-only, both-violating and neither-violating counts. Their total equals valid paired hours. Paired disagreement is (A-only + alternative-only) / retained hours. Rate fields are fractions unless a column explicitly says percent or pp; plotted axes show percentages. Signed voltage/loss differences use alternative minus A; the signed marginal violation difference uses A minus alternative. These quantities must not be interchanged.

The original stage contains 108 scenario-summary rows, 56 paired rows, 24 fixed-mapping threshold/exclusion rows and 24 resampling-estimate rows. The extension contains 120 alternative-mapping paired rows (including reused A/B) and 320 matched threshold/exclusion rows.

## Manuscript assets

`manuscript_assets/figures/Figure1_source.csv`: 80 rows for two feeders × 20 alternative mappings × two matched inputs. Mapping 0 is excluded. `FigureS1_source.csv`: six fixed-mapping paired disagreement estimates and conditional 2.5th–97.5th percentiles from 2,000 seven-day paired resamples. `TableS1_source.csv`–`TableS9_source.csv` are the exact formatted supplementary-table source values. Frozen CSVs in `manuscript_assets/evidence/` retain full numeric precision.

## Controls and interpretation

B-G multiplies B by the full-record global A/B energy ratio; B-Z multiplies each B column by its corresponding full-record ratio. Both remain estimated representations. Main settings: alpha 0.25, beta 0.5, EV power factor 1, common anchor 126.91314 MW, lower/upper voltage thresholds 0.95/1.05 p.u. Thresholds are study scenarios. A zero disagreement rate means matching decisions and does not necessarily mean zero violations.

Neither A nor B is independent metered ground truth. Mappings are conditional synthetic scenarios, not empirical replicates. Resampling ranges describe the observed record and are not population confidence intervals. The v1.1 extension was specified after inspecting v1.0 results; it was not an original publicly preregistered analysis.
