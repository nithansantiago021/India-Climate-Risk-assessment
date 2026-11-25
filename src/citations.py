"""In-app method, licence, citation and limitation text.

The strings live in one module so the About tab, the README and the repository
licence cannot drift into different descriptions of the same data. Markdown is
returned rather than rendered so the same text can be tested or reused outside
Streamlit. URLs are imported from ``config`` to keep a single source of truth.
"""

from src.config import (CC_BY_SA_URL, CMIP6_DESIGN_DOI, CMIP6_HISTORICAL_DOI,
                        CMIP6_SSP126_DOI, CMIP6_SSP245_DOI, CMIP6_SSP585_DOI,
                        EQM_GUDMUNDSSON_DOI, EQM_THEMESSL_DOI, IMD_DOI, IMD_TERMS_URL,
                        IMDLIB_URL, MIT_URL, MRI_MODEL_DOI)


def method_markdown() -> str:
    """Return the data pipeline and analysis method as Markdown.

    The steps mirror the bias-correction notebook exactly: monthly aggregation,
    bilinear regridding, additive EQM, Tmean derivation, anomaly baselines,
    OLS trends and district assignment. The final paragraph states the
    stationarity assumption explicitly, because the correction is trained once
    on 1995-2014 and then held fixed through 2100. Keeping the method here
    means a reviewer can audit the app without opening the notebook, while the
    notebook remains the executable audit trail for the same sequence.
    """
    return """
## Method

1. Mask the IMD 99.9 missing flag and average daily Tmax and Tmin to monthly
   means.
2. Crop MRI-ESM2.0 historical and scenario `tasmax` / `tasmin` to India,
   convert Kelvin to Celsius, and regrid bilinearly to the IMD one-degree grid.
3. Train additive empirical quantile mapping (EQM) against IMD for 1995-2014,
   separately for Tmax and Tmin, per calendar month and grid cell, using 20
   quantiles.
4. Apply the trained correction to every scenario with constant extrapolation
   at the edges, then derive Tmean as the mean of corrected Tmax and Tmin.
5. Compute anomalies against the IMD 1995-2014 monthly climatology and annual
   means for 2015-2100.
6. Fit per-cell OLS trends of annual means in degrees Celsius per decade and
   report two-sided p-values.
7. Assign each land grid cell to the district containing its centre; a district
   without an interior cell centre takes the nearest land cell within about
   110 km.
8. Export one compressed NetCDF file per scenario and variable for the app.

The correction is trained once on 1995-2014 and held fixed through 2100. The
main validation tables are in-sample, so they confirm that the fit converged;
the notebook's split-sample check (train 1995-2004, test 2005-2014) adds an
out-of-sample check but is still not a skill score for 2015-2100.
""".strip()


def citation_markdown() -> str:
    """Return dataset, software and method citations as Markdown.

    The model and experiment DOIs are listed separately from the model
    description because CMIP6 data users should cite both the experiment and
    the model paper. The IMD observation paper and the ``imdlib`` software
    paper are also separate: ``imdlib`` is an MIT-licensed retrieval client,
    while the observations themselves remain under IMD and Government of India
    terms. The bias-correction references describe the additive EQM variant
    used by the notebook.
    """
    return f"""
## Citations

**CMIP6 model and experiments**

- Eyring, V. et al. (2016). Overview of the Coupled Model Intercomparison
  Project Phase 6 (CMIP6). *Geoscientific Model Development*, 9, 1937-1958.
  {CMIP6_DESIGN_DOI}
- Yukimoto, S. et al. (2019). The Meteorological Research Institute Earth
  System Model version 2.0, MRI-ESM2.0. *Journal of the Meteorological Society
  of Japan*, 97(5), 931-965. {MRI_MODEL_DOI}
- MRI-ESM2.0 historical experiment, member `r1i1p1f1`, grid `gn`.
  {CMIP6_HISTORICAL_DOI}
- MRI-ESM2.0 SSP1-2.6 experiment, member `r1i1p1f1`, grid `gn`.
  {CMIP6_SSP126_DOI}
- MRI-ESM2.0 SSP2-4.5 experiment, member `r1i1p1f1`, grid `gn`.
  {CMIP6_SSP245_DOI}
- MRI-ESM2.0 SSP5-8.5 experiment, member `r1i1p1f1`, grid `gn`.
  {CMIP6_SSP585_DOI}

**Observations and retrieval software**

- Srivastava, A. K., Rajeevan, M. and Kshirsagar, S. R. (2009). Development of
  a high resolution daily gridded temperature data set (1969-2005) for the
  Indian region. *Atmospheric Science Letters*, 10(4), 249-254. {IMD_DOI}
- Nandi, S. et al. (2024). imdlib: A Python package for IMD gridded data.
  *Environmental Modelling & Software*, 171, 105869. {IMDLIB_URL}
- India Meteorological Department, Government of India. IMD one-degree gridded
  Tmax and Tmin observations, 1995-2014. {IMD_TERMS_URL}

**Bias correction**

- Gudmundsson, L. et al. (2012). Technical note: Downscaling RCM precipitation
  to the station scale using statistical transformations. *Hydrology and Earth
  System Sciences*, 16, 3383-3390. {EQM_GUDMUNDSSON_DOI}
- Themeßl, M. J., Gobiet, A. and Leuprecht, A. (2011). Empirical-statistical
  downscaling and error correction of daily precipitation from regional
  climate models. *International Journal of Climatology*, 31, 1530-1544. {EQM_THEMESSL_DOI}
""".strip()


def license_markdown() -> str:
    """Return the licence and attribution table as Markdown.

    The table separates four legal layers that are often conflated: the MIT
    licence on this repository's code, the MIT licence on the ``imdlib``
    retrieval client, the IMD and Government of India terms on the observed
    data, and the CC BY-SA 4.0 licence on the CMIP6 inputs and derived NetCDF
    products. The ShareAlike sentence is deliberate: the derived products in
    ``data/netcdf/`` are distributed under the same licence as the MRI-ESM2.0
    inputs, with attribution to both MRI and IMD.
    """
    return f"""
## Licensing and attribution

Application source code is released under the MIT License. The `imdlib`
retrieval client is also MIT-licensed, but it is a software dependency only;
the IMD observations it downloads remain under IMD and Government of India
open data terms.

The CMIP6 MRI-ESM2.0 inputs and the derived bias-corrected NetCDF products in
`data/netcdf/` are shared under the Creative Commons Attribution-ShareAlike
4.0 International licence (CC BY-SA 4.0). The ShareAlike condition is satisfied
by distributing the derived products under the same licence.

| Material | Licence | Attribution |
|---|---|---|
| Application code | MIT | Nithan B S |
| `imdlib` Python client | MIT | Nandi et al. (2024) |
| IMD gridded observations | IMD / Government of India open data terms | India Meteorological Department |
| CMIP6 MRI-ESM2.0 inputs | CC BY-SA 4.0 | Meteorological Research Institute (MRI), JMA; WCRP CMIP6 |
| Derived NetCDF products in `data/netcdf/` | CC BY-SA 4.0 | This project; MRI (CMIP6) and IMD |
| District boundaries | Source repository terms | HariKumarValluru |

Links: [MIT]({MIT_URL}) · [CC BY-SA 4.0]({CC_BY_SA_URL}) ·
[IMD]({IMD_TERMS_URL}).
""".strip()


def limitations_markdown() -> str:
    """Return the interpretation limits and caveats as Markdown.

    The caveats are kept next to the citations rather than hidden in a separate
    document. They describe the single-model design, the monthly rather than
    daily correction, the stationarity assumption, the derived Tmean, the
    one-degree district aggregation, the independence assumption behind the
    p-values and the third-party boundary source. A reviewer should read the
    displayed warming as one model's bias-corrected response, not as a
    multi-model consensus or a formal probabilistic risk estimate.
    """
    return """
## Limitations

- Single model: MRI-ESM2.0 only. Results reflect one model's climate
  sensitivity, not an inter-model spread or a probabilistic ensemble.
- Monthly, not daily: EQM corrects monthly means, so the app says nothing about
  heatwave-day counts or daily extremes.
- Stationarity: the 1995-2014 correction is held fixed through 2100.
- Tmean is derived as the mean of corrected Tmax and Tmin, not a true 24-hour
  observed mean.
- District values are means of assigned one-degree cells. Small districts can
  share a cell and therefore share a value.
- Trend p-values assume independent annual values; serial correlation makes
  them somewhat optimistic.
- The district boundary file is a third-party compilation and is not an
  official Survey of India boundary.

The app is a research and communication tool. It is not a substitute for a
multi-model ensemble, a formal attribution study or a site-level risk
assessment. Users should pair the maps with local observations and sector
expertise before making adaptation decisions.
""".strip()
