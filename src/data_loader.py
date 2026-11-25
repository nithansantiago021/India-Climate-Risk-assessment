"""Cached, silent data access for the Streamlit application."""

import json
import re
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import shapely
import streamlit as st
import xarray as xr

from src.config import MAX_NEAREST_M, VARS


@st.cache_data(show_spinner=False)
def discover_scenarios(nc_dir: Path) -> dict[str, dict[str, Path]]:
    """Return complete scenario groups found in ``nc_dir``.

    A scenario is complete only when Tmax, Tmean and Tmin NetCDF files are all
    present. The function is cached because directory scans happen on every
    rerun, while the result only changes when the exported products change.
    Filenames are matched with an explicit pattern instead of positional
    splitting so a scenario name containing underscores remains valid.
    Incomplete scenarios are silently skipped rather than rendered as broken
    options in the sidebar.
    """
    directory = Path(nc_dir)
    if not directory.exists():
        return {}
    found: dict[str, dict[str, Path]] = {}
    pattern = re.compile(r"(.+)_(tmax|tmean|tmin)_bias_corrected\.nc$")
    for path in sorted(directory.glob("*_bias_corrected.nc")):
        match = pattern.match(path.name)
        if match is None:
            continue
        scenario, variable = match.groups()
        found.setdefault(scenario, {})[variable] = path
    complete: dict[str, dict[str, Path]] = {}
    # Keep only scenarios that expose all three temperature variables.
    for scenario, variables in sorted(found.items()):
        if set(variables) == set(VARS):
            complete[scenario] = {
                variable: variables[variable] for variable in VARS
            }
    return complete


@st.cache_data(show_spinner=False)
def load_scenario(paths: tuple[Path, ...], mtimes: tuple[float, ...]) -> dict:
    """Load one scenario's annual means and annual anomalies into memory.

    ``mtimes`` is part of the cache key so an exported NetCDF file that is
    rewritten in place invalidates the cached arrays. The return value keeps
    plain NumPy arrays, which makes downstream trend and map code independent
    of xarray indexing details. Arrays use the shared ``(year, lat, lon)``
    layout expected by the analytics and figure modules, and the scenario
    files are checked for a common shape before they are returned. A shape
    mismatch raises immediately instead of producing a subtly misaligned map
    on a later rerun. All returned arrays are float64 for stable aggregation,
    and the cached object contains no open file handles.
    """
    _ = mtimes
    annual: dict[str, np.ndarray] = {}
    anomaly: dict[str, np.ndarray] = {}
    years = latitude = longitude = None
    # Read one variable at a time so each file handle closes promptly.
    for variable, path in zip(VARS, paths):
        with xr.open_dataset(path) as dataset:
            annual[variable] = dataset[f"{variable}_annual"].transpose("year", "lat", "lon").values.astype(float)
            anomaly[variable] = dataset[f"{variable}_anomaly_annual"].transpose("year", "lat", "lon").values.astype(float)
            if years is None:
                years = dataset["year"].values.astype(int)
                latitude = dataset["lat"].values.astype(float)
                longitude = dataset["lon"].values.astype(float)
    expected = annual["tmax"].shape
    if any(annual[variable].shape != expected for variable in VARS):
        raise ValueError("Scenario files do not share one grid and time axis")
    return {"annual": annual, "anom": anomaly, "years": years, "lat": latitude, "lon": longitude}


@st.cache_data(show_spinner=False)
def load_geo(source: str | Path) -> tuple[pd.DataFrame, dict]:
    """Load district metadata and a simplified GeoJSON payload.

    The source may be a local GeoJSON path or the upstream URL. Geometries are
    repaired because the published boundary file contains a few invalid
    polygons, then simplified to keep the browser payload small enough for
    responsive sliders and map redraws. Metadata is returned separately from
    the geometry so tables and map traces can share one stable identifier
    without carrying polygon coordinates through every calculation. The
    simplified geometry keeps the district outlines recognisable.
    """
    districts = gpd.read_file(source)
    districts["geometry"] = districts.geometry.make_valid()
    districts = districts.reset_index(drop=True)
    districts["uid"] = districts.index.astype(str)
    meta = pd.DataFrame(
        {
            "uid": districts["uid"],
            "state": districts["st_nm"],
            "district": districts["district"],
        }
    )
    meta[["minx", "miny", "maxx", "maxy"]] = districts.bounds.values
    # Simplify only after repairing invalid rings, then snap to a fixed grid.
    simplified = districts[["uid", "geometry"]].copy()
    simplified["geometry"] = shapely.set_precision(
        simplified.geometry.simplify(0.02, preserve_topology=True).values,
        0.001,
    )
    return meta, json.loads(simplified.to_json())


@st.cache_resource(show_spinner=False)
def build_weights(
    geo_path: str | Path,
    lat: tuple[float, ...],
    lon: tuple[float, ...],
    land_bytes: bytes,
) -> np.ndarray:
    """Build a row-normalised district-by-cell averaging matrix.

    A cell is assigned to the district containing its centre; a district with no interior cell centre takes the nearest land cell within about 110 km.
    """
    districts = gpd.read_file(geo_path)
    districts["geometry"] = districts.geometry.make_valid()
    districts = districts.reset_index(drop=True)
    lon_grid, lat_grid = np.meshgrid(np.asarray(lon), np.asarray(lat))
    land = np.frombuffer(land_bytes, dtype=bool)
    cells = gpd.GeoDataFrame({"cell": np.arange(lat_grid.size)},
                             geometry=gpd.points_from_xy(lon_grid.ravel(), lat_grid.ravel()),
                             crs=districts.crs)[land]
    weights = np.zeros((len(districts), lat_grid.size))
    inside = gpd.sjoin(cells, districts[["geometry"]], predicate="within")
    weights[inside["index_right"].values, inside["cell"].values] = 1
    empty = np.where(weights.sum(axis=1) == 0)[0]
    if len(empty):
        representatives = gpd.GeoDataFrame({"district": empty}, index=empty,
                                           geometry=districts.geometry.iloc[empty].representative_point(),
                                           crs=districts.crs).to_crs("EPSG:7755")
        nearest = gpd.sjoin_nearest(representatives, cells.to_crs("EPSG:7755"), max_distance=MAX_NEAREST_M)
        nearest = nearest[~nearest.index.duplicated()]
        weights[nearest["district"].values, nearest["cell"].values] = 1
    totals = weights.sum(axis=1, keepdims=True)
    return np.divide(weights, totals, out=np.zeros_like(weights), where=totals > 0)


@st.cache_resource(show_spinner=False)
def build_cell_geojson(
    lat: tuple[float, ...], lon: tuple[float, ...], land_bytes: bytes
) -> dict:
    """Return one square polygon per land grid cell for the native-resolution map.

    The payload is generated once per process and reused for every slider move.
    Cell identifiers follow the flattened row-major grid index, which matches
    the order used by the weighted series and district aggregation helpers.
    Each polygon is one native grid box, so the layer exposes the resolution
    of the IMD grid instead of implying district-level model output. Ocean
    cells are omitted entirely, keeping the GeoJSON payload compact.
    """
    latitudes = np.asarray(lat)
    longitudes = np.asarray(lon)
    # Use the mean spacing so irregular grids still produce square cells.
    half_y = abs(np.diff(latitudes)).mean() / 2
    half_x = abs(np.diff(longitudes)).mean() / 2
    land = np.frombuffer(land_bytes, dtype=bool).reshape(len(latitudes), len(longitudes))
    # Iterate in row-major order so the feature id equals the flattened cell index.
    features = []
    for row in range(len(latitudes)):
        for column in range(len(longitudes)):
            if not land[row, column]:
                continue
            y, x = latitudes[row], longitudes[column]
            ring = [[x - half_x, y - half_y], [x + half_x, y - half_y], [x + half_x, y + half_y],
                    [x - half_x, y + half_y], [x - half_x, y - half_y]]
            features.append({"type": "Feature", "id": str(row * len(longitudes) + column),
                             "properties": {}, "geometry": {"type": "Polygon", "coordinates": [ring]}})
    return {"type": "FeatureCollection", "features": features}
