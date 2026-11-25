"""Streamlit UI helpers for controls, metrics, tables and attribution."""

import numpy as np
import pandas as pd
import streamlit as st

from src.analytics import to_districts
from src.citations import (citation_markdown, license_markdown, limitations_markdown,
                           method_markdown)
from src.config import (ALL_INDIA, ANNUAL, DEFAULT_VARIABLE, DOWNLOAD_CSV_LABEL, ICON_AREA,
                        ICON_CONTROLS, ICON_DISPLAY, ICON_DOWNLOAD, LAYER_CELLS, LAYER_DISTRICTS,
                        METRICS, METRIC_SHORT, TABLE_NOTE, TREND, VARIABLE_CHOICES, VAR_SHORT,
                        VARS, scenario_label)


def render_sidebar(meta: pd.DataFrame, scenarios: list[str], years: np.ndarray) -> dict:
    """Render every control in one place and return a plain settings dictionary.

    The sidebar deliberately has no file-path inputs, reload buttons or loading
    status messages. Data are discovered from repository-relative paths by the
    loader, so the controls only describe the analytical view: scenario, area,
    variable, metric, time window and map layer.
    """
    st.sidebar.title(f"{ICON_CONTROLS} Controls")
    st.sidebar.caption("Scenario, area and display settings")
    scenario = st.sidebar.selectbox("Scenario", scenarios, format_func=scenario_label)
    st.sidebar.divider()
    st.sidebar.subheader(f"{ICON_AREA} Area")
    states = [ALL_INDIA] + sorted(meta["state"].unique())
    state = st.sidebar.selectbox("State / UT", states)
    district_uid = None
    district_name = None
    if state != ALL_INDIA:
        names = sorted(meta.loc[meta["state"] == state, "district"])
        district_name = st.sidebar.selectbox("District", ["All districts"] + names,
                                             key=f"district_{state}")
        if district_name != "All districts":
            district_uid = meta.loc[(meta["state"] == state)
                                    & (meta["district"] == district_name), "uid"].iloc[0]
        else:
            district_name = None
    area_label = f"{district_name}, {state}" if district_name else state
    st.sidebar.divider()
    st.sidebar.subheader(f"{ICON_DISPLAY} Display")
    variable_choice = st.sidebar.radio("Variable", VARIABLE_CHOICES, horizontal=True,
                                      index=VARIABLE_CHOICES.index(DEFAULT_VARIABLE))
    metric = st.sidebar.radio("Show", METRICS)
    ymin, ymax = int(years.min()), int(years.max())
    year, period = ymin, (ymin, ymax)
    if metric == ANNUAL:
        year = st.sidebar.slider("Year", ymin, ymax, min(max(2050, ymin), ymax))
    else:
        period = st.sidebar.slider("Period", ymin, ymax, (max(2021, ymin), min(2050, ymax)))
    layer = st.sidebar.radio("Map layer", [LAYER_DISTRICTS, LAYER_CELLS], horizontal=True,
                             help="Grid cells show the native ~1 degree IMD grid; districts "
                                  "average the cells assigned to each district.")
    chosen = VARS if variable_choice == DEFAULT_VARIABLE else (variable_choice.lower(),)
    return {"scenario": scenario, "state": state, "district_uid": district_uid,
            "district_name": district_name, "area_label": area_label,
            "variable_choice": variable_choice, "chosen": chosen, "metric": metric,
            "year": year, "period": period, "layer": layer}


def render_metrics(fields: dict[str, np.ndarray], chosen: tuple[str, ...], weights: np.ndarray,
                   area_label: str, metric: str, when: str) -> None:
    """Show one headline number per selected variable for the current area.

    The metric uses the same weighted mean as the district and grid layers, so
    the number above a map always matches the field drawn below it. A region
    with no valid cells shows an explicit "no data" value rather than a zero
    that could be mistaken for a real temperature.

    The helper receives the already-selected fields instead of recomputing
    them, which keeps the map and the headline number on exactly the same
    year or period. Formatting is deliberately compact: one decimal place is
    below the meaningful precision of a one-degree bias-corrected grid, and
    the sign is retained for anomalies and trends.
    """
    columns = st.columns(len(chosen))
    for column, variable in zip(columns, chosen):
        field = fields[variable].ravel()
        valid = np.isfinite(field)
        if valid.any() and weights[valid].sum() > 0:
            value = float((field[valid] * weights[valid]).sum() / weights[valid].sum())
            formatted = f"{value:+.2f}" if metric != ANNUAL else f"{value:.2f}"
            column.metric(f"{VAR_SHORT[variable]} · {area_label}", formatted,
                          help=f"{METRIC_SHORT[metric]}, {when}")
        else:
            column.metric(f"{VAR_SHORT[variable]} · {area_label}", "no data",
                          help="No IMD grid cell lies within about 110 km of this area.")
    if not np.any(weights > 0):
        st.warning("No IMD grid cell lies within about 110 km of this district, so no "
                   "value can be shown for it.")


def render_district_table(fields: dict[str, np.ndarray], chosen: tuple[str, ...],
                          meta: pd.DataFrame, weights: np.ndarray, state: str,
                          scenario: str, metric: str, when: str) -> None:
    """Render the sortable district values table and its CSV download button.

    Values are aggregated with the same district matrix used by the map, then
    rounded once at presentation time. The table is filtered to the selected
    state but keeps every district row so a reviewer can compare neighbours
    without changing the sidebar selection.

    The first value column is used for the default sort, which puts the
    warmest districts first for anomaly and trend views. The download uses
    the same frame as the on-screen table, so a reviewer never has to wonder
    whether the CSV and the visible rows were filtered differently.
    """
    table = meta[["state", "district"]].rename(
        columns={"state": "State", "district": "District"}).copy()
    unit = "°C/decade" if metric == TREND else "°C"
    for variable in chosen:
        table[f"{VAR_SHORT[variable]} ({unit})"] = np.round(
            to_districts(fields[variable].ravel(), weights), 3)
    if state != ALL_INDIA:
        table = table[table["State"] == state]
    sort_column = table.columns[2]
    table = table.sort_values(sort_column, ascending=False)
    st.caption(TABLE_NOTE)
    st.dataframe(table, use_container_width=True, hide_index=True)
    st.download_button(DOWNLOAD_CSV_LABEL, table.to_csv(index=False).encode(),
                       file_name=f"{scenario}_{METRIC_SHORT[metric].lower().replace(' ', '_')}_{when}.csv",
                       icon=ICON_DOWNLOAD)


def render_methodology(scenario: str, area_label: str) -> None:
    """Render the method, licence, citation and limitation panel.

    The same text is used by README.md, so the app and the repository cannot
    drift into different descriptions of the data. The panel is intentionally
    prose-light: a reviewer should be able to trace every dataset and every
    transformation without opening the notebook.

    The attribution block names the CMIP6 model, the IMD observations, the
    district boundary source and the derived NetCDF products. Each row states
    the creator, the period or version, the licence link and the modifications
    made here. The method section explains the EQM training window, the Tmean
    derivation, the anomaly baseline and the district aggregation rule.

    Limitations are kept next to the citations rather than hidden in a
    separate document. In particular, the correction is trained once on
    1995-2014 and assumed stationary through 2100; the main validation is
    in-sample and a split-sample check covers 2005-2014. A reviewer should
    read the displayed warming as one model's bias-corrected response, not as
    a multi-model consensus or a formal probabilistic risk estimate. The panel
    is the canonical in-app citation surface for both datasets and method
    references.
    """
    st.subheader("About this assessment")
    st.caption(f"Scenario {scenario_label(scenario)} · area {area_label}")
    st.caption("Bias correction is trained on 1995-2014 and held fixed through 2100.")
    st.markdown(method_markdown())
    st.divider()
    st.markdown(license_markdown())
    st.markdown(citation_markdown())
    st.markdown(limitations_markdown())
