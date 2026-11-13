# Reproducing the saved analysis

## Environment

The recorded computation used Python 3.12.14, NumPy 2.3.5, pandas 2.2.3 and SciPy 1.17.0. Formal figures used Matplotlib 3.10.8. Install the pinned dependencies from `requirements.txt` in a separate environment. Floating-point last digits and font layout may vary across platforms.

## Restore a separate working copy

Extract `analysis_archive/Traffic_Power_Analysis_v1_1.zip` into a fresh directory. Open a terminal in that extracted directory. Windows PowerShell commands follow.

```powershell
$env:PYTHONUTF8 = '1'
$env:OPENBLAS_NUM_THREADS = '1'
$env:OMP_NUM_THREADS = '1'
python -X utf8 code/restore_base.py
python -X utf8 code/check_saved_results.py
```

UTF-8 mode is required for the original scripts and their subprocesses on Windows because some archived paths contain Chinese characters. Restoration downloads two hash-pinned MATPOWER case files and requires internet access. The checker compares the saved extension arrays, paired decisions and reused original results.

## Rerun the extension

After restoration, run the following in the same working directory and environment.

```powershell
python -X utf8 code/run_addendum.py
python -X utf8 code/check_saved_results.py
python -X utf8 code/build_report.py
```

These commands recompute the 80 extension scenarios and update local results and logs. The extension relies on the original frozen A/B outputs. Preserve those original results for the extension comparison.

## Independently rerun the original 108 scenarios

Use an additional fresh copy of the restored `base_v1` directory. Open the terminal in that copy, set the environment variables above, and run the following.

```powershell
python -X utf8 code/run_analysis.py
python -X utf8 code/plot_results.py
python -X utf8 code/build_results_report.py
```

Compare this independent rerun with the archived record using numerical tolerances. Execution timestamps and generated-byte hashes will reflect the new run.

## Formal manuscript figures

Copy `manuscript_assets/` into a separate working directory. From its root run the following.

```powershell
python -X utf8 code/plot_figures.py
```

The optional `--audit-root` argument points to external QA helpers. Ordinary figure generation uses the packaged source data and runs with the pinned plotting dependency.

## Historical evidence

The nested archive contains the original locked plans, hash manifests and execution evidence. Preserve these as the historical record. Locking and packaging scripts document how that record was created. Scientific reproduction runs the analysis and checker commands above. The outer `verify_release.py` checks the deposited files and saved-array structure.
