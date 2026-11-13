# Supporting data and code

Research companion to **Sensitivity of hourly voltage decisions to charging energy representations in distribution test feeders** by Mingming Dong, Ge Chen and Wei Chen.

Version 1.0.0. Correspondence to Mingming Dong at milestonedad@gmail.com.

## Contents

| Path | Contents |
| --- | --- |
| `source_data/` | Paired estimated hourly charging inputs, zone-to-bus mappings, quality flags and source hashes |
| `analysis_archive/Traffic_Power_Analysis_v1_1.zip` | Complete frozen analysis record, 188 scenario arrays, executable code, summaries and nested source checkpoints |
| `code/analysis_v1/` and `code/analysis_v1_1/` | Browsable copies of the original analysis scripts |
| `manuscript_assets/code/` | Formal figure-generation script |
| `manuscript_assets/figures/` | Figure exports and source CSVs for Figures 1/S1 and Tables S1–S9 |
| `manuscript_assets/evidence/` | Full-precision numerical summaries and analysis provenance |
| `DATA_DICTIONARY.md` | Variables, units, array shapes and interpretation |
| `licenses/` and `LICENSE` | Reuse terms and third-party attribution |
| `CITATION.cff` and `.zenodo.json` | Citation and archival metadata |
| `SHA256SUMS.json` and `verify_release.py` | File-integrity and saved-array checks |

The study covers 4,344 hourly records and 275 zones from 1 September 2022 through 28 February 2023. The 33-bus and 69-bus feeders use fixed mapping 0 and 20 alternative synthetic mappings. The original 108 scenarios and 80 extension scenarios contain 816,672 scenario-hours in total.

Both charging inputs are released energy estimates. The mappings describe conditional synthetic feeder scenarios. Decision disagreement measures the sensitivity of the voltage assessment to these representations. Interpret resampling intervals conditionally on the observed record. The extension plan was developed after examination of the original results.

## Quick verification

Use Python 3.12 with the dependencies in `requirements.txt`. From the repository root run the following commands.

```bash
python -m pip install -r requirements.txt
python -X utf8 verify_release.py
```

The verification checks member hashes, nested ZIP integrity and all 188 saved scenario arrays. Physical-model reproduction follows the separate instructions in `REPRODUCING.md`.

Read `source_data/paired_energy_inputs.npz` using `numpy.load(path, allow_pickle=False)`. The data dictionary specifies each variable and unit.

## Reproduce analyses and figures

Follow `REPRODUCING.md`. A fresh working copy protects the archived execution logs and numerical outputs. The restoration script downloads two pinned MATPOWER case files and checks their SHA-256 values. The saved inputs and results can be inspected offline.

The files under `code/` are browseable copies. Run the scripts from the directory structure restored from the frozen archive, as described in the reproduction guide.

## Provenance

- UrbanEV source commit `44f2aa0c8d89f192bce00bafb0def74a21b39c68`. Cite Li et al. (2025), UrbanEV, Scientific Data 12, 523. https://doi.org/10.1038/s41597-025-04874-4
- MATPOWER case-source commit `80b6e16f760f58721ad31221c7287c28259cd4ad`. The restoration script fetches `case33bw.m` and `case69.m` from their pinned official URLs. Cite Zimmerman et al. (2011). https://doi.org/10.1109/TPWRS.2010.2051168
- The nested historical checkpoint includes Song's exploratory network workbook with its CC BY 4.0 attribution. The final feeder calculations use the pinned MATPOWER cases. https://doi.org/10.6084/m9.figshare.26354131.v1
- Frozen analysis archive SHA-256 `1610dc723eed6614546c625ca5391832e1f82c37be2cb7bf3fa387ab45cf7641`.

The archive preserves historical stage reports. The completed extension is documented in its v1.1 report and the final manuscript source data.

## Authors

1. Mingming Dong — State-owned Assets Management Office, Shaanxi College of Communications Technology, Xi'an, China.
2. Ge Chen — School of Economics and Management, Shaanxi College of Communications Technology, Xi'an, China.
3. Wei Chen — Electric Power Research Institute, State Grid Shaanxi Electric Power Co., Ltd., Xi'an, China.

## Reuse and citation

Newly authored study code is licensed under MIT. Study-derived data, numerical results, tables, figures and accompanying documentation are licensed under CC BY 4.0. Third-party materials retain their source terms. `LICENSE` and `licenses/THIRD_PARTY_NOTICES.md` define the scope, including nested archives.

Use the authors, record title and version above when citing this research companion, together with its published Zenodo record identifier once available. Cite the original data and case sources when reusing those materials. Archival metadata describes this supporting research record and the associated manuscript title.

Repository URL https://github.com/milestonedad-lang/energies-charging-voltage-sensitivity
