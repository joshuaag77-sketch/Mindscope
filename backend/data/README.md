# MindScope Data Folder

This folder holds lightweight CSV assets for the MVP:

- `baseline_profile.csv`: contextual means and standard deviations for the core scoring features
- `scenario_centroids.csv`: normalized centroids used for the scenario adjustment layer
- `synthetic_windows.csv`: optional demo windows for quick scoring tests

## Regenerating from workbook source

You can regenerate all three CSVs from the synthetic Excel pack:

```powershell
cd backend
./scripts/generate_from_baseline_pack.ps1 `
  -SourceXlsx "C:\path\to\mindscope_synthetic_baseline_pack.xlsx" `
  -OutputDir "data"
```

This script builds:

- contextual baseline means/stds for core features (global + user rows)
- normalized scenario centroids aligned to overload-direction z-space
- synthetic 10-minute windows with ISO timestamps

The loaders are intentionally tolerant of minor schema variation. Supported patterns include:

- baseline means: `app_switch_count_mean`, `mean_app_switch_count`
- baseline stds: `app_switch_count_std`, `std_app_switch_count`
- scenario values: raw feature column names or `_z` variants

For the sample data, `day_of_week=global` maps to `-1` and acts as a fallback row for any weekday.
