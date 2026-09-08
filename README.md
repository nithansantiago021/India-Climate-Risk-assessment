# India Climate Warming Assessment using CMIP6 & SSP2-4.5

Physical climate risk analysis projecting mid-century warming across India using CMIP6 projections, benchmarked against a 1981–2010 historical baseline.

## Overview

This project quantifies how much India's districts are projected to warm by mid-century (2041–2070) under a moderate-emissions pathway (SSP2-4.5), relative to their own 1981–2010 historical baseline — not a single national average. The output is a district-level warming map built from CMIP6 model output.

- **Model:** MRI-ESM2-0
- **Scenario:** SSP2-4.5 (`ssp245`)
- **Variable:** `tas` (near-surface air temperature), monthly
- **Baseline period:** 1981–2010
- **Future period:** 2041–2070
- **Region:** India (6°N–37°N, 68°E–98°E), with district boundaries overlaid

## Repo structure

```
india-climate-risk-assessment/
│
├── data/                  # CMIP6 NetCDF files (not tracked in git — see Setup below)
├── tmax/                  # IMD gridded observed tmax .GRD files (bias-correction add-on only — not tracked in git)
├── notebooks/
│   ├── CMIP6_analysis.ipynb          # Full pipeline: load → convert units → anomaly → map
│   └── CMIP6_bias_correction.ipynb   # Add-on: bias-corrects the model against IMD observations before projecting (see below)
├── outputs/
│   └── india_warming_projection.png
└── README.md
```

## Methodology

1. **Load** historical (1850–2014) and SSP2-4.5 (2015–2100) `tas` NetCDF files for MRI-ESM2-0 and concatenate into a single continuous time series.
2. **Convert units** from Kelvin to Celsius and crop to the India bounding box.
3. **Compute per-pixel climatologies** for both the 1981–2010 baseline and the 2041–2070 future period, keeping the `lat`/`lon` grid intact throughout (rather than collapsing to a national average before differencing) — this ensures each grid cell is compared against its own local baseline, not the country-wide mean.
4. **Take the anomaly** (future − own local baseline) per pixel, then average across years to get a single warming map.
5. **Plot** the anomaly with district boundaries overlaid, annotated with the baseline/future periods, units, and the India-wide mean warming for quick reference.

## Setup

### 1. Environment

```bash
pip install xarray rioxarray geopandas matplotlib netcdf4
```

### 2. Data

#### CMIP6 Climate Data

Download the following CMIP6 `tas` (monthly, `Amon`) files for **MRI-ESM2-0**, variant `r1i1p1f1`, grid `gn`, from an [ESGF](https://esgf-node.llnl.gov/search/cmip6/) node, and place them in `data/`:

| Experiment | File pattern |
|---|---|
| Historical | `tas_Amon_MRI-ESM2-0_historical_r1i1p1f1_gn_185001-201412.nc` |
| SSP2-4.5 | `tas_Amon_MRI-ESM2-0_ssp245_r1i1p1f1_gn_201501-210012.nc` |

The NetCDF (`.nc`) climate data files are not included in this repository due to their large file size.

#### District Boundaries

The India district boundary GeoJSON used in this project is sourced from
[HariKumarValluru/India-Map-with-States-and-Districts-GeoJson](https://github.com/HariKumarValluru/India-Map-with-States-and-Districts-GeoJson).

### 3. Run

```bash
jupyter notebook notebooks/analysis.ipynb
```

## Notes / limitations

- Single-model (MRI-ESM2-0) analysis — no multi-model ensemble, so results reflect one model's climate sensitivity rather than an inter-model spread.
- SSP2-4.5 only; SSP5-8.5 or other scenarios would show a wider warming range.
- Anomalies are computed per grid cell, not per district polygon — district boundaries are an overlay for readability, not a zonal statistic.

---

## Add-on: bias-corrected variant (`CMIP6_bias_correction.ipynb`)

A second notebook, `notebooks/CMIP6_bias_correction.ipynb`, extends the analysis
above by bias-correcting the raw CMIP6 model output against IMD gridded observed
temperature data before projecting — the original `analysis.ipynb` pipeline above
is unchanged and still runs independently.

**What it adds:**

- **IMD observational data** — gridded daily maximum temperature (`tmax`), 1995–2014,
  loaded via [`imdlib`](https://pypi.org/project/imdlib/) from `tmax/`.
- **Bias correction** — Empirical Quantile Mapping (`xsdba`), trained per calendar
  month on the model/observation overlap, regridded onto the IMD grid.
- **Validation** (in-sample, against the 1995–2014 training period) — RMSE of raw
  vs. corrected model against IMD, a seasonal-cycle comparison, and a distribution
  overlay, all restricted to IMD's land-only footprint.
- **Anomalies computed against the observed baseline** rather than the model's own
  climatology — each grid cell's future value is compared against IMD's 1995–2014
  monthly climatology at that same cell.

**This notebook uses different periods and a different region box than `analysis.ipynb`:**

| | `analysis.ipynb` | `CMIP6_bias_correction.ipynb` |
|---|---|---|
| Baseline period | 1981–2010 (model climatology) | 1995–2014 (IMD observed climatology) |
| Future period | 2041–2070 (single window) | 2021–2050 (near-term) and 2071–2100 (long-term) |
| Region box | 6°N–37°N, 68°E–98°E | 8°N–37°N, 68°E–97°E |

### Additional setup for the add-on

```bash
pip install imdlib xsdba
```

Download the IMD `tmax` data and place the year-wise `.GRD` files (`1995.GRD`,
`1996.GRD`, ...) in `tmax/`:

```python
import imdlib as imd
imd.get_data("tmax", 1995, 2014, fn_format="yearwise")
```

The notebook itself reads these locally via `imd.open_data(...)` rather than
re-downloading on every run.

### Output

![India warming projection](outputs/india_warming_districts.png)

### Additional limitations (add-on only)

- Validation is **in-sample** — computed by reapplying the trained correction to
  its own training period, so it confirms the fit converged, not that it
  generalizes to the future projection.
- The correction is trained against IMD's daily-**maximum** `tmax`, while the
  CMIP6 variable being corrected is monthly-**mean** `tas` — these aren't
  strictly the same physical quantity, so treat absolute anomaly magnitudes
  with that in mind.
- Bias correction assumes stationarity — EQM assumes the model's bias structure
  learned on 1995–2014 remains valid through 2100.