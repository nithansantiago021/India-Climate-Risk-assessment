"""Shared configuration, paths, labels and license constants for the app."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
NC_DIR = DATA_DIR / "netcdf"
GEO_PATH = DATA_DIR / "districts.geojson"
GEO_URL = (
    "https://raw.githubusercontent.com/HariKumarValluru/"
    "India-Map-with-States-and-Districts-GeoJson/master/districts.geojson"
)

VARS = ("tmax", "tmean", "tmin")
VAR_LABELS = {
    "tmax": "Maximum (Tmax)",
    "tmean": "Mean (Tmean)",
    "tmin": "Minimum (Tmin)",
}
VAR_SHORT = {"tmax": "Tmax", "tmean": "Tmean", "tmin": "Tmin"}
BASELINE = "1995-2014"
ANNUAL = "Annual mean (°C)"
ANOMALY = f"Anomaly vs IMD {BASELINE} (°C)"
TREND = "Linear trend (°C per decade)"
METRICS = (ANNUAL, ANOMALY, TREND)
METRIC_SHORT = {ANNUAL: "Annual mean", ANOMALY: "Mean anomaly", TREND: "Trend"}
SCENARIO_LABELS = {
    "ssp126": "SSP1-2.6",
    "ssp245": "SSP2-4.5",
    "ssp370": "SSP3-7.0",
    "ssp585": "SSP5-8.5",
}
SCENARIO_COLORS = {
    "ssp126": "#2a9d8f",
    "ssp245": "#e9a100",
    "ssp370": "#e76f51",
    "ssp585": "#b5179e",
}
FALLBACK_COLORS = ("#264653", "#2a9d8f", "#e9c46a", "#f4a261", "#e76f51", "#6a4c93")
MAX_NEAREST_M = 110_000
MAP_HEIGHT = 560
MAP_WIDE = 700
MAP_NARROW = 420
COLORSCALE = "YlOrRd"
PAGE_TITLE = "India bias-corrected CMIP6 temperature"
PAGE_ICON = ":material/thermostat:"
LAYER_DISTRICTS = "Districts"
LAYER_CELLS = "Grid cells"

MODEL = "MRI-ESM2-0"
MEMBER = "r1i1p1f1"
SCENARIO_ORDER = ("ssp126", "ssp245", "ssp585")
NEAR = (2021, 2050)
LONG = (2071, 2100)
FUTURE = (2015, 2100)
NQUANTILES = 20
GRID_RESOLUTION = "~1° (~110 km)"
METHOD_NOTE = "EQM against IMD 1995-2014"

TAB_MAP = "Map"
TAB_TRENDS = "Trends"
TAB_ABOUT = "About"
ICON_CONTROLS = ":material/tune:"
ICON_AREA = ":material/location_on:"
ICON_DISPLAY = ":material/layers:"
ICON_MAP = ":material/map:"
ICON_TRENDS = ":material/show_chart:"
ICON_ABOUT = ":material/info:"
ICON_DOWNLOAD = ":material/download:"
ICON_THERMOMETER = ":material/thermostat:"
ICON_SCENARIO = ":material/timeline:"

DOWNLOAD_CSV_LABEL = "Download district values (CSV)"
DOWNLOAD_SERIES_LABEL = "Download annual series (CSV)"
SHARED_SCALE_NOTE = "Panels share one colour scale so values are directly comparable."
TABLE_NOTE = "District values are area means of the grid cells assigned to each district."
CHART_HEIGHT = 470
COLORBAR_LEN = 0.72
COLORBAR_THICKNESS = 12
MAP_MARGIN = dict(l=0, r=0, t=38, b=0)
CHART_MARGIN = dict(l=12, r=12, t=56, b=12)

CODE_LICENSE = "MIT"
DATA_LICENSE = "CC BY-SA 4.0"
MIT_URL = "https://opensource.org/license/mit"
CC_BY_SA_URL = "https://creativecommons.org/licenses/by-sa/4.0/"
IMD_TERMS_URL = "https://mausam.imd.gov.in/"
IMDLIB_URL = "https://doi.org/10.1016/j.envsoft.2023.105869"
IMD_DOI = "https://doi.org/10.1002/asl.232"
CMIP6_HISTORICAL_DOI = "https://doi.org/10.22033/ESGF/CMIP6.6842"
CMIP6_SSP126_DOI = "https://doi.org/10.22033/ESGF/CMIP6.6909"
CMIP6_SSP245_DOI = "https://doi.org/10.22033/ESGF/CMIP6.6910"
CMIP6_SSP585_DOI = "https://doi.org/10.22033/ESGF/CMIP6.6929"
MRI_MODEL_DOI = "https://doi.org/10.2151/jmsj.2019-051"
CMIP6_DESIGN_DOI = "https://doi.org/10.5194/gmd-9-1937-2016"
EQM_GUDMUNDSSON_DOI = "https://doi.org/10.5194/hess-16-3383-2012"
EQM_THEMESSL_DOI = "https://doi.org/10.1002/joc.2168"
DERIVED_NC_PATTERN = "*_bias_corrected.nc"
DERIVED_VARIABLES = ("tmax", "tmean", "tmin")
EQM_METHOD = "Additive Empirical Quantile Mapping (EQM)"
DATA_LICENSE_NOTE = "Derived NetCDF products are shared under CC BY-SA 4.0."
CODE_LICENSE_NOTE = "Application source code is released under the MIT License."
P_FLOOR = 0.001
TREND_MIN_YEARS = 3
MAP_OPACITY = 0.8
SCENARIO_PREFIX = "ssp"
CMIP6_EXPERIMENTS = ("historical", "ssp126", "ssp245", "ssp585")
IMD_VARIABLES = ("tmax", "tmin")
DISTRICT_SOURCE = "HariKumarValluru/India-Map-with-States-and-Districts-GeoJson"
README_TITLE = "India Climate Risk Assessment"
DEPLOYMENT_TARGET = "Streamlit Community Cloud"
LICENSE_SECTION = "Licensing and attribution"
ALL_INDIA = "All India"
VARIABLE_CHOICES = ("Tmax", "Tmean", "Tmin", "All three")
DEFAULT_VARIABLE = "All three"
DEFAULT_SCENARIO = "ssp245"
DEFAULT_LAYER = LAYER_DISTRICTS
MAP_STYLE = "carto-positron"
UNITS = "°C"
TREND_UNITS = "°C/decade"
PERIOD_NEAR = "2021-2050"
PERIOD_LONG = "2071-2100"
PERIOD_FULL = "2015-2100"
NOTEBOOK_PATH = ROOT / "notebooks" / "CMIP6_bias_correction.ipynb"
VALIDATION_NOTE = "Validation is in-sample and confirms fit convergence, not future skill."


def scenario_label(name: str) -> str:
    """Return the publication label for a scenario identifier.

    The filesystem and cache keys use compact lowercase identifiers such as
    ``ssp245``. The interface and README use the IPCC-style labels such as
    ``SSP2-4.5``. Keeping the mapping here prevents the two conventions from
    drifting across the sidebar, figure legends and exported CSV names.

    Unknown identifiers are returned in uppercase rather than raising, which
    lets a new scenario file appear without a code change. The function also
    accepts already-formatted labels, so callers can safely pass either form.
    The normalisation removes dashes and underscores before lookup, so
    ``SSP2-4.5``, ``ssp245`` and ``ssp_245`` resolve to the same label. This
    keeps file names, cache keys and display text independent.
    """
    if not isinstance(name, str) or not name.strip():
        raise ValueError("Scenario identifier must be a non-empty string")
    key = name.strip().lower().replace("-", "").replace("_", "")
    aliases = {
        "ssp126": "SSP1-2.6",
        "ssp245": "SSP2-4.5",
        "ssp370": "SSP3-7.0",
        "ssp585": "SSP5-8.5",
    }
    if key in aliases:
        return aliases[key]
    for scenario, label in SCENARIO_LABELS.items():
        if scenario.replace("-", "") == key:
            return label
    return name.strip().upper()
