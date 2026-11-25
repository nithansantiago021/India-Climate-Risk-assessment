"""Composition helpers for the map, trend and about tabs."""

import numpy as np
import pandas as pd
import streamlit as st

from src.analytics import field_for, to_districts
from src.config import (ANNUAL, ANOMALY, BASELINE, DOWNLOAD_SERIES_LABEL, ICON_DOWNLOAD,
                        LAYER_DISTRICTS, MAP_NARROW, MAP_WIDE, METRIC_SHORT, P_FLOOR,
                        SHARED_SCALE_NOTE, TREND, VARS, VAR_SHORT, scenario_label)
from src.data_loader import load_scenario
from src.figures import make_map, map_frame, trend_data, trend_figure
from src.ui import render_district_table, render_methodology, render_metrics


def render_map_tab(data: dict, files: dict, controls: dict, meta: pd.DataFrame,
                   geojson: dict, cell_geojson: dict, district_weights: np.ndarray,
                   region_weight: np.ndarray, lat_flat: np.ndarray,
                   lon_flat: np.ndarray, land_flat: np.ndarray) -> None:
    """Render the headline metrics, map panels and district table.

    Every panel uses one field selection and one shared value range across
    scenarios, so a three-variable row is directly comparable. Fixed heights and panel widths keep the cards aligned.
    """
    chosen = controls["chosen"]
    metric, year, period = controls["metric"], controls["year"], controls["period"]
    when = str(year) if metric == ANNUAL else f"{period[0]}-{period[1]}"
    if metric == TREND and period[1] - period[0] < 2:
        st.warning("Pick a period of at least 3 years to fit a trend.")
    fields = {variable: field_for(data, variable, metric, year, period)
              for variable in chosen}
    render_metrics(fields, chosen, region_weight, controls["area_label"], metric, when)
    values = {variable: to_districts(fields[variable].ravel(), district_weights)
              if controls["layer"] == LAYER_DISTRICTS else fields[variable].ravel()
              for variable in chosen}
    blocks = [values[variable][np.isfinite(values[variable])] for variable in chosen]
    for name, scenario_files in files.items():
        if name == controls["scenario"]:
            continue
        paths = tuple(scenario_files[variable] for variable in VARS)
        other = load_scenario(paths, tuple(path.stat().st_mtime for path in paths))
        for variable in chosen:
            field = field_for(other, variable, metric, year, period)
            series = (to_districts(field.ravel(), district_weights)
                      if controls["layer"] == LAYER_DISTRICTS else field.ravel())
            blocks.append(series[np.isfinite(series)])
    finite = np.concatenate(blocks) if blocks else np.array([])
    vmin, vmax = (float(finite.min()), float(finite.max())) if finite.size else (0.0, 1.0)
    if vmax - vmin < 1e-6:
        vmax = vmin + 1e-6
    panel_w = MAP_WIDE if len(chosen) == 1 else MAP_NARROW
    columns = st.columns(len(chosen))
    for column, variable in zip(columns, chosen):
        label = "Temperature (°C)" if metric == ANNUAL else (
            "Anomaly (°C)" if metric == ANOMALY else "Trend (°C/decade)")
        frame = map_frame(values[variable], controls["layer"], label, meta, lat_flat,
                          lon_flat, land_flat, controls["state"])
        figure = make_map(frame, controls["layer"], f"{VAR_SHORT[variable]} · "
                          f"{METRIC_SHORT[metric]}, {when}", label, meta, geojson,
                          cell_geojson, controls["state"], controls["district_uid"],
                          panel_w, (vmin, vmax))
        column.plotly_chart(figure, use_container_width=True)
    st.caption(SHARED_SCALE_NOTE)
    render_district_table(fields, chosen, meta, district_weights, controls["state"],
                          controls["scenario"], metric, when)


def render_trend_tab(files: dict, controls: dict, weights: np.ndarray,
                     area_label: str) -> None:
    """Render the multi-scenario annual series, trend fits and download table.

    Scenarios are loaded through the same cached loader as the map, so
    switching between tabs does not reread NetCDF files. The fit window is the
    sidebar period unless the annual-mean metric is active, in which case a
    dedicated slider lets the reviewer choose a different window without
    changing the map above.
    """
    st.subheader("Trend analysis")
    scenarios = list(files)
    left, right = st.columns([3, 2])
    selected = left.multiselect("Scenarios to compare", scenarios, default=scenarios,
                                format_func=scenario_label)
    mode = right.radio("Values", ["Absolute (°C)", f"Anomaly vs IMD {BASELINE} (°C)"],
                       horizontal=True)
    key = "annual" if mode.startswith("Absolute") else "anom"
    t0, t1 = controls["period"]
    if controls["metric"] == ANNUAL:
        t0, t1 = st.slider("Trend fit period", int(min(controls["period"])),
                           int(max(controls["period"])), (int(min(controls["period"])),
                                                         int(max(controls["period"]))))
    else:
        st.caption(f"Trend lines are fitted over the sidebar period ({t0}-{t1}).")
    if not selected:
        st.caption("Select at least one scenario to compare.")
        return
    if t1 - t0 < 2:
        st.warning("Pick a period of at least 3 years to fit a trend.")
        return
    datasets = {}
    for scenario in selected:
        paths = tuple(files[scenario][variable] for variable in VARS)
        datasets[scenario] = load_scenario(paths, tuple(path.stat().st_mtime for path in paths))
    trend = trend_data(datasets, selected, weights, key, t0, t1)
    st.plotly_chart(trend_figure(trend, key), use_container_width=True)
    render_trend_table(trend, area_label)


def render_trend_table(trend: dict, area_label: str) -> None:
    """Render the OLS summary table and the long-form annual series download.

    The summary uses the fit objects produced for the figure, so the numbers
    in the table and the dashed lines in the chart cannot disagree. The long
    table keeps every year and scenario, which makes the download useful for
    a reviewer who wants to refit or replot the series outside Streamlit.

    The p-value is the two-sided test for slope = 0. It assumes independent
    annual values, so serial correlation makes it somewhat optimistic; that
    caveat is stated in the About tab rather than hidden in the table. The
    download uses a long layout because a wide one would repeat the year axis
    for every scenario and variable, which is harder to reshape later. The
    table is only rendered when at least one fit exists, so an empty summary
    does not produce a confusing blank dataframe. Formatting is applied with
    pandas Styler so the underlying numeric values remain sortable and the
    CSV export is unaffected by the display precision. A reviewer can sort by
    trend, p-value or mean without losing the scenario labels, and the table
    scrolls horizontally on narrow screens.
    """
    st.markdown("**Linear trend over the selected period** (OLS on annual means; "
                "dashed lines above)")
    summary = pd.DataFrame(trend["summary"])
    if not summary.empty:
        mean_column = [column for column in summary.columns if column.startswith("Mean ")][0]
        st.dataframe(summary.style.format({
            "Trend (°C/decade)": "{:+.3f}",
            "p-value": lambda value: "< 0.001" if value < P_FLOOR else f"{value:.4f}",
            mean_column: "{:.2f}",
        }), use_container_width=True, hide_index=True)
    long = pd.DataFrame(trend["long"])
    st.download_button(DOWNLOAD_SERIES_LABEL, long.to_csv(index=False).encode(),
                       file_name=f"trend_series_{area_label.replace(', ', '_').replace(' ', '_')}.csv",
                       icon=ICON_DOWNLOAD)


def render_about_tab(scenario: str, area_label: str) -> None:
    """Render the method, citation and limitation panel for the About tab.

    The tab is intentionally the only place in the app that carries long-form
    provenance text. Keeping it out of the sidebar means the analytical view
    stays uncluttered while the full MIT and CC BY-SA 4.0 attribution remains
    one click away for a reviewer.

    The at-a-glance table gives a hiring manager the model, scenarios,
    reference dataset, baseline and resolution without requiring them to read
    the method prose first. The longer method and citation blocks then provide
    the audit trail: EQM training window, Tmean definition, anomaly baseline,
    district assignment rule, dataset creators, licence links and the
    modifications made in this repository.

    The scenario and area labels are passed in so the panel always describes
    the view the reviewer is currently looking at, rather than a static
    project-level summary that could drift from the selected controls.
    """
    st.markdown("""
**At a glance**

| Item | Value |
|---|---|
| Model | MRI-ESM2-0 (`tasmax` / `tasmin`) |
| Scenarios | SSP1-2.6, SSP2-4.5, SSP5-8.5 |
| Reference observations | IMD 1-degree gridded Tmax / Tmin |
| Training and anomaly baseline | 1995-2014 |
| Projection window | 2015-2100 |
| Native resolution | ~1 degree (about 110 km) |
""")
    render_methodology(scenario, area_label)
