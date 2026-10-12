"""Read saved data. Prefers the full pull in data/raw/, falls back to data/sample/.

This is the one place the app, notebooks and tests should load data from.
"""

import json
from pathlib import Path

import pandas as pd

from pipeline.sources import HOUSTON_DMS, LA_TICKETS, RAW_DIR, SAMPLE_DIR

LOCAL_TZ = "America/Chicago"
LA_DATE_FIELDS = ("Load_Date", "Disposal_Date")


def resolve_path(filename: str, prefer_raw: bool = True) -> Path:
    """Return data/raw/<filename> if it exists (and preferred), else data/sample/<filename>."""
    raw = RAW_DIR / filename
    if prefer_raw and raw.exists():
        return raw
    sample = SAMPLE_DIR / filename
    if sample.exists():
        return sample
    raise FileNotFoundError(f"{filename} not found in {RAW_DIR} or {SAMPLE_DIR}. Run pipeline.ingest first.")


def load_la_tickets(prefer_raw: bool = True) -> pd.DataFrame:
    """Load Louisiana load tickets with epoch-ms dates converted to US/Central datetimes."""
    df = pd.read_parquet(resolve_path(LA_TICKETS.filename, prefer_raw))
    for col in LA_DATE_FIELDS:
        df[col] = pd.to_datetime(df[col], unit="ms", utc=True).dt.tz_convert(LOCAL_TZ)
    df["Ticket"] = df["Ticket"].astype("Int64")  # source stores ticket IDs as doubles
    return df


def load_houston_dms(prefer_raw: bool = True) -> dict:
    """Load Houston debris management sites as a GeoJSON FeatureCollection dict."""
    return json.loads(resolve_path(HOUSTON_DMS.filename, prefer_raw).read_text())


def geojson_properties(collection: dict) -> pd.DataFrame:
    """Flatten a FeatureCollection's properties into a DataFrame (one row per feature)."""
    return pd.DataFrame([f.get("properties", {}) for f in collection.get("features", [])])
