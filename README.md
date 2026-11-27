# India Climate Risk Assessment: Bias-Corrected CMIP6 Temperature Projections

A district-level physical climate risk assessment for India built from bias-corrected CMIP6 temperature projections (MRI-ESM2.0), delivered as an interactive Streamlit application for scenario comparison, spatial exploration, and data export.

## Overview

The application quantifies near-term (`2021–2050`) and long-term (`2071–2100`) warming across India relative to an observed `1995–2014` India Meteorological Department (IMD) baseline at both native 1° grid resolution and district boundaries (730 mapped districts).

### Key Capabilities
- **Temperature Variables:** Maximum ($T_{\max}$), Mean ($T_{\text{mean}}$), and Minimum ($T_{\min}$) temperature.
- **Emissions Scenarios:** `SSP1-2.6`, `SSP2-4.5`, and `SSP5-8.5`.
- **Time Horizons:** Near-term (`2021–2050`) and long-term (`2071–2100`) vs. `1995–2014` baseline.
- **Spatial & Statistical Views:** Interactive 1° grid and district choropleth maps, annual mean, warming anomaly, decadal OLS linear trends (°C/decade with two-sided $p$-values), regional time-series comparisons, and CSV downloads.

---

## Key Findings

India-wide land area-weighted $T_{\text{mean}}$ anomalies relative to the IMD `1995–2014` baseline:

| Scenario | Near-Term (2021–2050) | Long-Term (2071–2100) | Linear Trend (2015–2100) |
| :--- | ---: | ---: | ---: |
| **SSP1-2.6** | +0.79 °C | +1.24 °C | +0.104 °C/decade |
| **SSP2-4.5** | +0.75 °C | +1.81 °C | +0.222 °C/decade |
| **SSP5-8.5** | +0.97 °C | +3.50 °C | +0.498 °C/decade |

- **Regional Warming Hotspots:** High-altitude Himalayan districts experience the strongest projected warming—led under `SSP5-8.5` (`2071–2100`) by Leh (+4.38 °C), Ganderbal (+4.35 °C), and Srinagar (+4.33 °C), and under `SSP2-4.5` by Leh (+2.32 °C), Pithoragarh (+2.31 °C), and Lahaul and Spiti (+2.30 °C).

---

## Repository Structure

```text
India-Climate-Risk-assessment/
├── app.py                          # Streamlit application entrypoint
├── src/
│   ├── config.py                   # Paths, labels, figure constants, and metadata
│   ├── citations.py                # Methodology, data attribution, and licensing text
│   ├── data_loader.py              # Cached NetCDF, GeoJSON, and spatial weight loaders
│   ├── analytics.py                # Trend calculations and district/state/national aggregation
│   ├── figures.py                  # Synchronized Plotly choropleth maps and trend plots
│   ├── ui.py                       # Sidebar controls, KPI metrics, and district tables
│   └── tabs.py                     # Map, Trends, and About view composition
├── data/
│   ├── districts.geojson           # District boundary geometries
│   └── netcdf/                     # Bias-corrected NetCDF climate products (9 files)
├── notebooks/
│   ├── CMIP6_analysis.ipynb        # Exploratory temperature anomaly mapping
│   └── CMIP6_bias_correction.ipynb # Empirical Quantile Mapping (EQM) pipeline & validation
├── packages.txt                    # System geospatial/netCDF dependencies
└── requirements.txt                # Python dependencies
```

---

## Methodology

1. **Observational Reference:** Processed IMD daily gridded $T_{\max}$ and $T_{\min}$ (`1995–2014`, 1° resolution) into monthly climatologies.
2. **CMIP6 Preprocessing:** Cropped MRI-ESM2.0 (`r1i1p1f1`, `gn`) historical and scenario (`SSP1-2.6`, `SSP2-4.5`, `SSP5-8.5`) outputs to India, converted Kelvin to Celsius, and bilinearly regridded to the 1° IMD grid.
3. **Bias Correction:** Trained additive Empirical Quantile Mapping (`xsdba.EmpiricalQuantileMapping`, 20 quantiles per calendar month and grid cell) on `1995–2014` (validated via `1995–2004` / `2005–2014` split-sample testing), applied to `2015–2100` projections, and derived $T_{\text{mean}}$.
4. **Spatial Aggregation & Trends:** Computed anomalies, decadal OLS warming trends, and area-weighted district/state/national summaries.

---

## Quickstart

### Run Locally
```bash
git clone https://github.com/nithansantiago021/India-Climate-Risk-assessment.git
cd India-Climate-Risk-assessment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

### Regenerate Derived NetCDF Products (Optional)
Pre-computed bias-corrected NetCDF files are included in `data/netcdf/`. To reproduce them from raw ESGF CMIP6 and `imdlib` inputs:
```bash
pip install imdlib xsdba matplotlib jupyter
jupyter notebook notebooks/CMIP6_bias_correction.ipynb
cp outputs/netcdf/*_bias_corrected.nc data/netcdf/
```

---

## Data Sources & Licensing

- **Application Code:** Licensed under the [MIT License](LICENSE).
- **CMIP6 Climate Projections:** MRI-ESM2.0 outputs (Meteorological Research Institute, JMA / WCRP CMIP6) and derived NetCDF products in `data/netcdf/` are distributed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).
- **Observational Baseline:** IMD 1° gridded temperature data (`1995–2014`) retrieved via `imdlib` (MIT) and used under [India Meteorological Department / Government of India](https://mausam.imd.gov.in/) open data terms.
- **District Boundaries:** 2011 census district geometries sourced from [HariKumarValluru](https://github.com/HariKumarValluru) and simplified for web mapping.

### Key References
- Eyring, V. et al. (2016). Overview of CMIP6. *Geoscientific Model Development*, 9, 1937–1958.
- Yukimoto, S. et al. (2019). The Meteorological Research Institute Earth System Model version 2.0, MRI-ESM2.0. *Journal of the Meteorological Society of Japan*, 97(5), 931–965.
- Srivastava, A. K., Rajeevan, M., & Kshirsagar, S. R. (2009). High-resolution daily gridded temperature dataset for the Indian region. *Atmospheric Science Letters*, 10(4), 249–254.
- Gudmundsson, L. et al. (2012). Downscaling RCM precipitation to the station scale using statistical transformations. *Hydrology and Earth System Sciences*, 16, 3383–3390.