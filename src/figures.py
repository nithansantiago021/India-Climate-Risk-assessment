"""Map and trend figures with shared scales and consistent dimensions."""

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy import stats

from src.analytics import weighted_series
from src.config import (ALL_INDIA, CHART_HEIGHT, CHART_MARGIN, COLORBAR_LEN, COLORBAR_THICKNESS,
                        COLORSCALE, FALLBACK_COLORS, LAYER_DISTRICTS, MAP_HEIGHT, MAP_MARGIN,
                        MAP_OPACITY, MAP_STYLE, MAP_WIDE, SCENARIO_COLORS, VAR_LABELS, VAR_SHORT,
                        VARS, scenario_label)


def view_for(bounds: tuple[float, float, float, float], panel_w: int = MAP_WIDE,
             height: int = MAP_HEIGHT):
    """Return a map centre and zoom level for a geographic bounding box.

    The zoom estimate converts the box width and height into tile pixels and
    takes the more restrictive of the two, then subtracts a small margin so
    labels are not clipped at the panel edge. The result is clamped to the
    range supported by the basemap so tiny districts and the full country both
    render sensibly. Keeping this calculation in one place means every map
    panel uses the same framing rules, whether it shows one variable or three.
    The panel width is passed in rather than read from global state so the
    single-panel and three-panel layouts can share this function.

    The 1.25 factor on the vertical estimate compensates for the extra
    vertical room taken by the map title and colorbar. The small 0.3 zoom
    subtraction leaves a margin around the selected geometry so district
    outlines do not touch the panel edge. Both constants are intentionally
    local: they describe this figure style, not the data. The returned center
    dictionary matches the structure expected by Plotly's MapLibre layout, so
    callers do not need to know whether the map is a district or cell layer.
    Bounds are supplied as ``(minx, miny, maxx, maxy)`` in degrees.
    """
    minx, miny, maxx, maxy = bounds
    width = max(maxx - minx, 0.5)
    height_deg = max(maxy - miny, 0.5)
    zoom_x = np.log2(panel_w * 360 / (512 * width))
    zoom_y = np.log2(height * 360 / (512 * height_deg * 1.25))
    zoom = float(np.clip(min(zoom_x, zoom_y) - 0.3, 2.5, 9))
    center = {"lat": (miny + maxy) / 2, "lon": (minx + maxx) / 2}
    return center, zoom


def map_frame(values: np.ndarray, layer: str, label: str, meta: pd.DataFrame,
              lat_flat: np.ndarray, lon_flat: np.ndarray, land_flat: np.ndarray,
              state: str) -> pd.DataFrame:
    """Build the tabular payload for one district or grid-cell map layer.

    District rows carry the stable ``uid`` used by the GeoJSON feature ids and
    the state filter. Grid-cell rows carry the flattened cell index, latitude
    and longitude for hover text. The frame is built before the figure so the
    same values can be reused by the headline metrics and the download table.
    The function also keeps the state filter in one place: the map, the table
    and the district selector therefore show exactly the same set of rows.
    Grid-cell frames intentionally ignore the state filter because the native
    layer is a national raster rather than a political boundary view.

    Values are passed in already flattened to the grid's cell order, so the
    district branch aligns by position while the cell branch subsets with the
    land mask. This avoids a spatial join in the render path and keeps every
    rerun predictable even when the user drags a year slider quickly. The
    returned frame is plain pandas so it can also feed the CSV download
    without converting between GeoPandas and Plotly row models.
    """
    if layer == LAYER_DISTRICTS:
        frame = pd.DataFrame({"uid": meta["uid"], "State": meta["state"],
                              "District": meta["district"], label: values})
        if state != ALL_INDIA:
            frame = frame[frame["State"] == state]
        return frame
    index = np.where(land_flat)[0]
    return pd.DataFrame({"cell": index.astype(str), label: values[index],
                         "Lat": lat_flat[index], "Lon": lon_flat[index]})


def make_map(frame: pd.DataFrame, layer: str, title: str, label: str,
             meta: pd.DataFrame, geojson: dict, cell_geojson: dict, state: str,
             district_uid: str | None, panel_w: int,
             value_range: tuple[float, float]) -> go.Figure:
    """Render one choropleth panel with a shared range and fixed geometry.
    Panels share height, margins, opacity and colorbar thickness; ``value_range`` keeps side-by-side variables directly comparable.
    """
    vmin, vmax = value_range
    if layer == LAYER_DISTRICTS:
        figure = px.choropleth_map(
            frame, geojson=geojson, locations="uid", featureidkey="properties.uid",
            color=label, hover_name="District", hover_data={"State": True, label: ":.2f", "uid": False},
            color_continuous_scale=COLORSCALE, range_color=(vmin, vmax), opacity=MAP_OPACITY, map_style=MAP_STYLE)
    else:
        figure = px.choropleth_map(
            frame, geojson=cell_geojson, locations="cell", color=label,
            hover_data={"Lat": ":.1f", "Lon": ":.1f", label: ":.2f", "cell": False},
            color_continuous_scale=COLORSCALE, range_color=(vmin, vmax), opacity=MAP_OPACITY, map_style=MAP_STYLE)
    if district_uid is not None and layer == LAYER_DISTRICTS:
        figure.add_trace(go.Choroplethmap(
            geojson=geojson, locations=[district_uid], z=[0], featureidkey="properties.uid",
            showscale=False, hoverinfo="skip", colorscale=[[0, "rgba(0,0,0,0)"], [1, "rgba(0,0,0,0)"]],
            marker=dict(line=dict(color="#111111", width=3))))
    if district_uid is not None:
        row = meta.iloc[int(district_uid)]
        bounds = (row.minx, row.miny, row.maxx, row.maxy)
    elif state != ALL_INDIA:
        subset = meta[meta["state"] == state]
        bounds = (subset.minx.min(), subset.miny.min(), subset.maxx.max(), subset.maxy.max())
    else:
        bounds = (meta.minx.min(), meta.miny.min(), meta.maxx.max(), meta.maxy.max())
    center, zoom = view_for(bounds, panel_w, MAP_HEIGHT)
    figure.update_layout(map=dict(center=center, zoom=zoom), height=MAP_HEIGHT, margin=MAP_MARGIN,
        font=dict(family="sans-serif", size=12), title=dict(text=title, x=0.01, font=dict(size=14)),
        coloraxis_colorbar=dict(title=dict(text=label), thickness=COLORBAR_THICKNESS, len=COLORBAR_LEN))
    return figure


def trend_data(datasets: dict[str, dict], selected: list[str], weights: np.ndarray,
               key: str, t0: int, t1: int) -> dict:
    """Compute weighted annual series and OLS fits for the trend tab.

    ``key`` selects absolute annual means or anomalies. Each scenario and
    variable gets a weighted series, a fit over the inclusive period, and one
    long-form row per year for the downloadable CSV. Scenarios with fewer than
    three valid years are retained in the series but omitted from the fit table.
    The shared year axis is read from the first selected scenario; every
    scenario in the exported set is aligned to the same 2015-2100 calendar.
    """
    series, fits, summary, long_rows = {}, {}, [], []
    years = datasets[selected[0]]["years"]
    for scenario in selected:
        data = datasets[scenario]
        series[scenario] = {}
        fits[scenario] = {}
        for variable in VARS:
            values = weighted_series(data[key][variable], weights)
            series[scenario][variable] = values
            mask = (data["years"] >= t0) & (data["years"] <= t1) & np.isfinite(values)
            fit = stats.linregress(data["years"][mask], values[mask]) if mask.sum() >= 3 else None
            fits[scenario][variable] = fit
            if fit is not None:
                summary.append({"Scenario": scenario_label(scenario), "Variable": VAR_SHORT[variable],
                                "Trend (°C/decade)": fit.slope * 10, "p-value": fit.pvalue,
                                f"Mean {t0}-{t1} (°C)": float(np.mean(values[mask]))})
            long_rows.extend({"scenario": scenario, "variable": variable, "year": int(year),
                              key: float(value)} for year, value in zip(data["years"], values))
    return {"series": series, "fits": fits, "summary": summary, "long": long_rows, "years": years, "t0": t0, "t1": t1}


def trend_figure(trend: dict, key: str) -> go.Figure:
    """Render the three-variable annual series with dashed OLS trend lines.

    The figure shares height, margins and hover behaviour with the map cards.
    Anomaly panels add a zero line; absolute panels do not, because zero
    degrees Celsius is not a meaningful baseline for the annual mean.
    """
    figure = make_subplots(rows=1, cols=3, subplot_titles=[VAR_LABELS[v] for v in VARS], shared_yaxes=False, horizontal_spacing=0.06)
    years = trend["years"]
    for scenario, variables in trend["series"].items():
        color = SCENARIO_COLORS.get(scenario, FALLBACK_COLORS[0])
        for column, variable in enumerate(VARS, start=1):
            figure.add_trace(go.Scatter(
                x=years, y=variables[variable], mode="lines", name=scenario_label(scenario),
                legendgroup=scenario, showlegend=column == 1, line=dict(color=color, width=1.8),
                hovertemplate="%{x}: %{y:.2f} °C<extra>" + scenario_label(scenario) + "</extra>"), row=1, col=column)
            fit = trend["fits"][scenario][variable]
            if fit is None: continue
            mask = (years >= trend["t0"]) & (years <= trend["t1"])
            figure.add_trace(go.Scatter(
                x=years[mask], y=fit.intercept + fit.slope * years[mask], mode="lines",
                name=f"{scenario_label(scenario)} trend", legendgroup=scenario, showlegend=False,
                line=dict(color=color, width=2, dash="dash"),
                hovertemplate=f"trend {fit.slope * 10:+.3f} °C/decade<extra>{scenario_label(scenario)}</extra>"), row=1, col=column)
    figure.update_xaxes(title_text="Year")
    figure.update_yaxes(title_text="°C", col=1)
    if key == "anom":
        for column in (1, 2, 3): figure.add_hline(y=0, line=dict(color="grey", width=1), row=1, col=column)
    figure.update_layout(height=CHART_HEIGHT, margin=CHART_MARGIN, hovermode="x unified", font=dict(family="sans-serif", size=12), legend=dict(orientation="h", y=1.12, x=0))
    return figure
