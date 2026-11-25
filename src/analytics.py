"""Numerical helpers for trends, regional weights and district aggregation."""

import numpy as np
import pandas as pd

from src.config import ALL_INDIA, ANNUAL, ANOMALY


def trend_per_decade(values: np.ndarray, years: np.ndarray) -> np.ndarray:
    """Return the ordinary least squares slope in °C per decade for each cell.

    ``values`` is a ``(year, lat, lon)`` array and ``years`` is its matching
    one-dimensional year axis. The calculation is vectorised over the grid:
    the year axis is centred once, then multiplied by the centred field so no
    per-cell Python loop is needed. Cells that are entirely NaN remain NaN,
    which keeps the ocean and unreachable district cells out of the maps.

    The slope is multiplied by ten because the input years are annual but the
    displayed unit is degrees Celsius per decade. A zero denominator would
    mean a degenerate time axis, so that case returns NaN rather than dividing
    by zero. The result is a plain array that can feed the map or table.
    """
    if values.ndim != 3:
        raise ValueError("Expected a (year, lat, lon) array")
    if len(years) != values.shape[0]:
        raise ValueError("Year axis does not match the field's first dimension")
    x = years.astype(float) - years.astype(float).mean()
    count = np.isfinite(values).sum(axis=0)
    mean = np.divide(np.nansum(values, axis=0), count,
                     out=np.zeros(values.shape[1:]), where=count > 0)
    y = values - mean
    denominator = float((x**2).sum())
    if denominator == 0:
        return np.full(values.shape[1:], np.nan)
    # The centred year vector broadcasts across every grid cell at once.
    slope = 10.0 * (x[:, None, None] * y).sum(axis=0) / denominator
    valid = np.isfinite(values).any(axis=0)
    return np.where(valid, slope, np.nan)


def field_for(
    data: dict, variable: str, metric: str, year: int, period: tuple[int, int]
) -> np.ndarray:
    """Select the two-dimensional field that the map should display.

    The annual metric uses a single year. The anomaly and trend metrics use
    the inclusive period selected in the sidebar. The function keeps the
    branch here rather than in the tab so the map and the headline metrics
    always read from exactly the same field.

    Annual means are read from the ``annual`` cube; anomalies come from the
    precomputed ``anom`` cube so the IMD baseline is applied once by the
    notebook rather than re-derived on every rerun. A trend is fitted on the
    annual means inside the selected period, so the map and the trend table
    describe the same quantity.
    """
    if variable not in data["annual"]:
        raise KeyError(f"Unknown variable: {variable}")
    years = data["years"]
    if metric == ANNUAL:
        selected = years == year
        if not selected.any():
            raise ValueError(f"Year {year} is not present in the scenario")
        return data["annual"][variable][selected][0]
    inside = (years >= period[0]) & (years <= period[1])
    if not inside.any():
        raise ValueError("The selected period contains no years")
    if metric == ANOMALY:
        return data["anom"][variable][inside].mean(axis=0)
    return trend_per_decade(data["annual"][variable][inside], years[inside])


def to_districts(field_flat: np.ndarray, weights: np.ndarray) -> np.ndarray:
    """Aggregate a flattened grid field to district means.

    ``weights`` is the row-normalised district-by-cell matrix built by the data
    loader. The numerator skips non-finite cells and the denominator counts
    only the finite cells that contribute to each district, so a district is
    never biased by ocean or missing cells that happen to fall in its row.

    The matrix product is used instead of a spatial join here because the
    weights are already fixed for the lifetime of the process. This keeps
    slider reruns cheap even when the map shows all three variables.

    Rows with no assigned cells produce NaN. That is intentional: a remote
    island district should not inherit the national mean or a neighbouring
    district's value just to avoid an empty cell in the table. The caller can
    then show "no data" with an explicit explanation.
    """
    if field_flat.ndim != 1:
        raise ValueError("Expected a flattened one-dimensional field")
    if weights.shape[1] != field_flat.size:
        raise ValueError("District weights and field have different cell counts")
    valid = np.isfinite(field_flat)
    numerator = weights @ np.where(valid, field_flat, 0.0)
    denominator = weights @ valid.astype(float)
    # Guard the division so districts without data become NaN, not zero.
    return np.where(
        denominator > 0,
        numerator / np.where(denominator > 0, denominator, 1.0),
        np.nan,
    )


def region_weights(
    state: str,
    district_uid: str | None,
    meta: pd.DataFrame,
    weights: np.ndarray,
    lat_flat: np.ndarray,
    land_flat: np.ndarray,
) -> np.ndarray:
    """Return a cell-weight vector for India, a state or a single district.

    A selected district reuses its row from the district matrix. A selected
    state combines every district row that belongs to it, then binarises the
    result so a cell shared by neighbouring districts is not counted twice.
    The All India option uses cosine-latitude weighting over land cells, which
    prevents the high-latitude grid boxes from being over-represented.

    The returned vector is normalised to sum to one, so callers can pass it
    directly to a weighted mean. An empty region keeps a zero vector, which
    the UI treats as "no data" rather than silently showing a national value.
    """
    if len(meta) != weights.shape[0]:
        raise ValueError("District metadata and weight rows do not align")
    if lat_flat.shape != land_flat.shape:
        raise ValueError("Latitude and land-mask arrays must have equal length")
    if district_uid is not None:
        cell_weights = weights[int(district_uid)].copy()
    elif state != ALL_INDIA:
        rows = np.where(meta["state"].values == state)[0]
        cell_weights = (weights[rows].sum(axis=0) > 0).astype(float)
    else:
        cell_weights = land_flat * np.cos(np.deg2rad(lat_flat))
    total = cell_weights.sum()
    return cell_weights / total if total > 0 else cell_weights


def weighted_series(values: np.ndarray, weights: np.ndarray) -> np.ndarray:
    """Collapse a ``(year, lat, lon)`` cube to a weighted annual series.

    The numerator and denominator both ignore non-finite cells, so a series
    remains defined even when part of the domain is masked. The denominator is
    guarded before division, which returns NaN for regions with no valid data
    instead of raising a warning or emitting a misleading zero.

    The field is reshaped to ``(year, cell)`` once; the same weights are then
    applied to every year. This is the operation behind the trend tab's
    country, state and district lines, so it is deliberately allocation-light
    and safe to call for several scenarios in one rerun. The output length is
    exactly the number of years in the input cube, which lets the figure code
    pair it directly with the shared year axis.
    """
    if values.ndim != 3:
        raise ValueError("Expected a (year, lat, lon) array")
    cells = values.shape[1] * values.shape[2]
    if weights.size != cells:
        raise ValueError("Weights and grid cells have different sizes")
    flat = values.reshape(values.shape[0], -1)
    valid = np.isfinite(flat)
    numerator = (np.where(valid, flat, 0.0) * weights).sum(axis=1)
    denominator = (valid * weights).sum(axis=1)
    # Zero-weight regions produce NaN rather than a divide-by-zero warning.
    return np.where(
        denominator > 0,
        numerator / np.where(denominator > 0, denominator, 1.0),
        np.nan,
    )
