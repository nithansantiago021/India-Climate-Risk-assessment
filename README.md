# India Climate Risk Assessment: Bias-Corrected CMIP6 Temperature Projections

A district-level climate risk assessment for India built from bias-corrected
CMIP6 temperature projections. The project quantifies near-term (2021-2050) and
long-term (2071-2100) warming relative to an observed 1995-2014 baseline, then
exposes the results through a Streamlit application for scenario comparison,
spatial exploration and CSV export.

The analytical question is deliberately local: how much does each district warm
under different emissions pathways, and where is the signal strongest? The app
answers that question on the native one-degree IMD grid and on district
boundaries, without collapsing the country to a single national average.

## What the application does

- Three variables: maximum (Tmax), mean (Tmean) and minimum (Tmin) temperature.
- Three scenarios: SSP1-2.6, SSP2-4.5 and SSP5-8.5.
- Two time windows: near-term 2021-2050 and long-term 2071-2100.
- Three map metrics: annual mean, anomaly against the IMD baseline, and linear
  trend in degrees Celsius per decade.
- Two spatial layers: native one-degree grid cells and district means.
- District, state and All India aggregation for headline metrics and series.
- Multi-scenario annual series with OLS trend fits, p-values and CSV downloads.
- Shared map heights, margins, colorbar geometry and a common color range across
  side-by-side panels and scenarios.

## Application and architecture

Entrypoint: `app.py`. Deployment target: Streamlit Community Cloud, pointed at
the repository root. The app discovers exported NetCDF products silently from
repository-relative paths; there are no file-path inputs, reload buttons or
loading banners in the UI.

```
India-Climate-Risk-assessment/
├── app.py                         # thin entrypoint: page config, data bootstrap, tabs
├── src/
│   ├── config.py                  # paths, labels, figure constants and licence metadata
│   ├── citations.py               # method, licence, citation and limitation text
│   ├── data_loader.py             # cached NetCDF, GeoJSON, district weights, cell polygons
│   ├── analytics.py               # trends, field selection, district and regional aggregation
│   ├── figures.py                 # shared-scale Plotly maps and trend figures
│   ├── ui.py                      # sidebar, headline metrics, district table, attribution
│   └── tabs.py                    # map, trends and about tab composition
├── data/
│   ├── districts.geojson          # tracked district boundaries
│   └── netcdf/                    # nine derived bias-corrected NetCDF products
├── notebooks/
│   ├── CMIP6_analysis.ipynb       # exploratory tas anomaly map
│   └── CMIP6_bias_correction.ipynb # reproducible EQM pipeline and validation
├── .streamlit/config.toml         # restrained theme and headless server defaults
├── packages.txt                   # Debian geospatial and netCDF libraries for deployment
├── requirements.txt
├── LICENSE
└── README.md
```

Every `src` module owns one responsibility and stays within a fixed size budget:
150-180 lines per module, fewer than six functions per module, and 30-50 lines
per function. `app.py` contains only wiring. The budgets are enforced during
review with an AST check rather than left as a style aspiration.

## Key findings

India-wide land area-weighted Tmean anomalies relative to the IMD 1995-2014
baseline, computed from the exported bias-corrected products:

| Scenario | Near-term 2021-2050 | Long-term 2071-2100 | Linear trend 2015-2100 |
|---|---:|---:|---:|
| SSP1-2.6 | +0.79 °C | +1.24 °C | +0.104 °C/decade |
| SSP2-4.5 | +0.75 °C | +1.81 °C | +0.222 °C/decade |
| SSP5-8.5 | +0.97 °C | +3.50 °C | +0.498 °C/decade |

The district table contains 732 districts, of which 730 have at least one
assigned land grid cell. Under SSP5-8.5 the strongest long-term Tmean warming
appears in Himalayan districts such as Leh (+4.38 °C), Ganderbal (+4.35 °C) and
Srinagar (+4.33 °C). Under SSP2-4.5 the leading districts are Leh (+2.32 °C),
Pithoragarh (+2.31 °C) and Lahaul and Spiti (+2.30 °C). The near-term ordering
across scenarios is not strictly monotonic because a single model run retains
internal variability; the long-term separation is the more robust signal.

## Data and licensing

The repository separates four legal layers that are often conflated: the MIT
licence on this repository's code, the MIT licence on the `imdlib` retrieval
client, the IMD and Government of India terms on the observed data, and the
CC BY-SA 4.0 licence on the CMIP6 inputs and derived NetCDF products.

| Material | Creator | Period / version | Licence | Modifications |
|---|---|---|---|---|
| Application code | Nithan B S | 2026 | [MIT](https://opensource.org/license/mit) | Original work |
| `imdlib` Python client | Nandi et al. | 2024 | MIT | Used only to retrieve IMD files |
| IMD one-degree gridded Tmax and Tmin | India Meteorological Department, Government of India | 1995-2014 | [IMD / Government of India open data terms](https://mausam.imd.gov.in/) | Daily values averaged to monthly means; used as the EQM reference and anomaly baseline |
| CMIP6 MRI-ESM2.0 `tasmax` and `tasmin` | Meteorological Research Institute (MRI), JMA; WCRP CMIP6 | 1850-2100 | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) | Cropped to India, converted to degrees Celsius, regridded to one degree, bias-corrected and annualised |
| Derived NetCDF products in `data/netcdf/` | This project | 2026 | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) | Derived from the datasets above; distributed under the same licence as the MRI-ESM2.0 inputs |
| India district boundaries | HariKumarValluru, GitHub | 2011 census | Source repository terms; attributed here | Geometry repaired, simplified and indexed for web mapping |

The derived NetCDF products in `data/netcdf/` are shared under CC BY-SA 4.0 to
satisfy the ShareAlike condition of the MRI-ESM2.0 CMIP6 input licence. They are
attributed jointly to the Meteorological Research Institute (MRI) for the CMIP6
model output and to the India Meteorological Department (IMD) for the
observational reference. `imdlib` is MIT-licensed as a Python retrieval client
only; the IMD observations it downloads remain under IMD and Government of India
terms and are not relicensed by this repository.

## Citations

### CMIP6 model and experiments

- Eyring, V. et al. (2016). Overview of the Coupled Model Intercomparison
  Project Phase 6 (CMIP6). *Geoscientific Model Development*, 9, 1937-1958.
  https://doi.org/10.5194/gmd-9-1937-2016
- Yukimoto, S. et al. (2019). The Meteorological Research Institute Earth
  System Model version 2.0, MRI-ESM2.0. *Journal of the Meteorological Society
  of Japan*, 97(5), 931-965. https://doi.org/10.2151/jmsj.2019-051
- MRI-ESM2.0 historical experiment, member `r1i1p1f1`, grid `gn`.
  https://doi.org/10.22033/ESGF/CMIP6.6842
- MRI-ESM2.0 SSP1-2.6 experiment, member `r1i1p1f1`, grid `gn`.
  https://doi.org/10.22033/ESGF/CMIP6.6909
- MRI-ESM2.0 SSP2-4.5 experiment, member `r1i1p1f1`, grid `gn`.
  https://doi.org/10.22033/ESGF/CMIP6.6910
- MRI-ESM2.0 SSP5-8.5 experiment, member `r1i1p1f1`, grid `gn`.
  https://doi.org/10.22033/ESGF/CMIP6.6929

### Observations and retrieval software

- Srivastava, A. K., Rajeevan, M. and Kshirsagar, S. R. (2009). Development of a
  high resolution daily gridded temperature data set (1969-2005) for the Indian
  region. *Atmospheric Science Letters*, 10(4), 249-254.
  https://doi.org/10.1002/asl.232
- Nandi, S. et al. (2024). imdlib: A Python package for IMD gridded data.
  *Environmental Modelling & Software*, 171, 105869.
  https://doi.org/10.1016/j.envsoft.2023.105869
- India Meteorological Department, Government of India. IMD one-degree gridded
  Tmax and Tmin observations, 1995-2014. https://mausam.imd.gov.in/

### Bias correction

The notebook trains `xsdba.EmpiricalQuantileMapping` with `kind="+"`, which is
additive empirical quantile mapping. The relevant references are:

- Gudmundsson, L. et al. (2012). Technical note: Downscaling RCM precipitation
  to the station scale using statistical transformations. *Hydrology and Earth
  System Sciences*, 16, 3383-3390. https://doi.org/10.5194/hess-16-3383-2012
- Themeßl, M. J., Gobiet, A. and Leuprecht, A. (2011). Empirical-statistical
  downscaling and error correction of daily precipitation from regional climate
  models. *International Journal of Climatology*, 31, 1530-1544.
  https://doi.org/10.1002/joc.2168

The same attribution block is rendered in the app's About tab from
`src/citations.py`, so the code and README cannot drift apart.

## Methodology

1. Load IMD daily Tmax and Tmin, mask the 99.9 missing flag and average to
   monthly means.
2. Load CMIP6 historical and scenario `tasmax` / `tasmin`, crop to India with a
   five-degree margin, convert Kelvin to Celsius, relabel timestamps to month
   start and regrid bilinearly to the IMD one-degree grid.
3. Train additive empirical quantile mapping (EQM) separately for Tmax and Tmin
   against IMD for 1995-2014, per calendar month and grid cell, using 20
   quantiles.
4. Apply the trained correction to every scenario with constant extrapolation at
   the edges, then derive Tmean as the mean of corrected Tmax and Tmin.
5. Compute anomalies against the IMD 1995-2014 monthly climatology and annual
   means for each year from 2015 to 2100.
6. Fit per-cell OLS trends of annual means in degrees Celsius per decade and
   compute two-sided p-values.
7. Assign each land grid cell to the district containing its centre. Districts
   without an interior cell centre take the nearest land cell within about
   110 km; remote islands with no reachable cell remain empty.
8. Export one compressed NetCDF file per scenario and variable, then render the
   cached products in the Streamlit app.

Validation in the notebook covers RMSE and bias before and after correction, a
seasonal-cycle comparison, distribution overlays and a split-sample check
(train 1995-2004, test 2005-2014). The main tables are in-sample; the
split-sample section is the out-of-sample check, so a lower corrected RMSE
there confirms that the correction generalises beyond the fitted years rather
than proving skill for 2015-2100.

## Local setup

```bash
git clone https://github.com/nithansantiago021/India-Climate-Risk-assessment.git
cd India-Climate-Risk-assessment
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

The app expects:

- `data/netcdf/{scenario}_{tmax|tmean|tmin}_bias_corrected.nc` for at least one
  complete scenario.
- `data/districts.geojson`, or network access to the upstream boundary URL as a
  fallback.

If the NetCDF products are absent, run the notebook and copy its
`outputs/netcdf/` products into `data/netcdf/`.

## Deploying to Streamlit Community Cloud

1. Push the repository to GitHub with `app.py` at the root.
2. Open <https://share.streamlit.io>, create a new app and select the repository
   and branch.
3. Set the main file path to `app.py`.
4. Leave secrets empty. The app reads only repository-relative data files.
5. Deploy. Streamlit installs `requirements.txt` and the Debian libraries listed
   in `packages.txt`; `.streamlit/config.toml` sets headless server defaults and
   the restrained light theme.

Every tracked data file is below the 50 MB GitHub limit: the nine NetCDF
products total about 28 MB and `data/districts.geojson` is about 4.9 MB. Raw
CMIP6 and IMD inputs are gitignored and should not be pushed.

## Reproducing the climate products

The notebook is retained as the audit trail for the data pipeline. It is not
required to run the app.

```bash
pip install imdlib xsdba matplotlib jupyter
jupyter notebook notebooks/CMIP6_bias_correction.ipynb
```

The notebook writes products to `outputs/netcdf/`. The deployed app reads
`data/netcdf/`, so copy the nine files after a successful run:

```bash
mkdir -p data/netcdf
cp outputs/netcdf/*_bias_corrected.nc data/netcdf/
```

Raw inputs are not tracked because of size:

- CMIP6 NetCDF files in `data/` (ignored).
- IMD year-wise `.GRD` files in `notebooks/tmax/` and `notebooks/tmin/`
  (ignored).

Download the CMIP6 files from an ESGF node for MRI-ESM2-0, member `r1i1p1f1`,
grid `gn`, experiments `historical`, `ssp126`, `ssp245` and `ssp585`. Download
the IMD files with `imdlib`:

```python
import imdlib as imd
imd.get_data("tmax", 1995, 2014, fn_format="yearwise")
imd.get_data("tmin", 1995, 2014, fn_format="yearwise")
```

## Limitations

- Single model: MRI-ESM2.0 only. Results reflect one model's climate
  sensitivity, not an inter-model spread or a probabilistic ensemble.
- Monthly, not daily: EQM corrects monthly means, so the app says nothing about
  heatwave-day counts or daily extremes.
- Stationarity assumption: the 1995-2014 correction is held fixed through 2100.
- Tmean is derived as the mean of corrected Tmax and Tmin, not a true 24-hour
  observed mean.
- District values are means of assigned one-degree cells. Small districts can
  share a cell and therefore share a value.
- Trend p-values assume independent annual values; serial correlation makes them
  somewhat optimistic.
- The district boundary file is a third-party compilation and is not an official
  Survey of India boundary.

## Repository checks

```bash
python -m compileall -q app.py src
python -c "import app"
streamlit run app.py --server.headless true
```

The release check also verifies the 150-180 line module budget, the fewer-than-six
functions rule, the 30-50 line function budget, zero emoji outside notebooks, and
that no tracked file exceeds 50 MB.
