"""Thin Streamlit entrypoint for the India climate risk assessment."""

import matplotlib
matplotlib.use("Agg")

import numpy as np
import streamlit as st

from src.analytics import region_weights
from src.config import (BASELINE, EQM_METHOD, GEO_PATH, GEO_URL, ICON_ABOUT, ICON_MAP,
                        ICON_TRENDS, MODEL, NC_DIR, PAGE_ICON, PAGE_TITLE, TAB_ABOUT,
                        TAB_MAP, TAB_TRENDS, VARS, scenario_label)
from src.data_loader import (build_cell_geojson, build_weights, discover_scenarios, load_geo,
                             load_scenario)
from src.tabs import render_about_tab, render_map_tab, render_trend_tab
from src.ui import render_sidebar


def main() -> None:
    """Bootstrap cached data, render the sidebar and dispatch the three tabs.

    The entrypoint owns only wiring: page configuration, silent data loading,
    the district and grid-cell weight matrices, and the tab layout. All
    analysis, figure construction and UI composition live in ``src`` so this
    file stays readable as the application grows.
    """
    st.set_page_config(page_title=PAGE_TITLE, page_icon=PAGE_ICON, layout="wide")
    files = discover_scenarios(NC_DIR)
    if not files:
        st.error("No complete set of Tmax, Tmean and Tmin bias-corrected NetCDF "
                 "files was found. Run the bias-correction notebook, then reload.")
        st.stop()
    first = next(iter(files))
    paths = tuple(files[first][variable] for variable in VARS)
    data = load_scenario(paths, tuple(path.stat().st_mtime for path in paths))
    geo_source = GEO_PATH if GEO_PATH.exists() else GEO_URL
    meta, geojson = load_geo(geo_source)
    land_flat = np.isfinite(data["annual"]["tmax"][0]).ravel()
    lon_grid, lat_grid = np.meshgrid(data["lon"], data["lat"])
    lat_flat, lon_flat = lat_grid.ravel(), lon_grid.ravel()
    district_weights = build_weights(geo_source, tuple(data["lat"]), tuple(data["lon"]),
                                     land_flat.tobytes())
    cell_geojson = build_cell_geojson(tuple(data["lat"]), tuple(data["lon"]),
                                      land_flat.tobytes())
    controls = render_sidebar(meta, list(files), data["years"])
    if controls["scenario"] != first:
        paths = tuple(files[controls["scenario"]][variable] for variable in VARS)
        data = load_scenario(paths, tuple(path.stat().st_mtime for path in paths))
    region_weight = region_weights(controls["state"], controls["district_uid"], meta,
                                   district_weights, lat_flat, land_flat)
    st.title(PAGE_TITLE)
    st.caption(f"{MODEL} · {EQM_METHOD} against IMD {BASELINE} · "
               f"{scenario_label(controls['scenario'])} · area: **{controls['area_label']}**")
    map_tab, trend_tab, about_tab = st.tabs(
        [f"{ICON_MAP} {TAB_MAP}", f"{ICON_TRENDS} {TAB_TRENDS}", f"{ICON_ABOUT} {TAB_ABOUT}"])
    with map_tab:
        render_map_tab(data, files, controls, meta, geojson, cell_geojson, district_weights,
                       region_weight, lat_flat, lon_flat, land_flat)
    with trend_tab:
        render_trend_tab(files, controls, region_weight, controls["area_label"])
    with about_tab:
        render_about_tab(controls["scenario"], controls["area_label"])


if __name__ == "__main__":
    main()
