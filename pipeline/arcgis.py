"""Minimal paginated client for ArcGIS REST `query` endpoints."""

import requests

from pipeline.sources import Source

TIMEOUT_S = 60


def fetch_page(source: Source, offset: int) -> dict:
    """Fetch one page of records starting at `offset`. Returns the parsed JSON."""
    params = {
        "where": "1=1",
        "outFields": ",".join(source.keep_fields),
        "orderByFields": "OBJECTID",  # stable order so pages don't overlap
        "resultOffset": offset,
        "resultRecordCount": source.page_size,
        "returnGeometry": "true" if source.geojson else "false",
        "f": "geojson" if source.geojson else "json",
    }
    resp = requests.get(source.url, params=params, timeout=TIMEOUT_S)
    resp.raise_for_status()
    data = resp.json()
    if "error" in data:
        raise RuntimeError(f"ArcGIS error for {source.name}: {data['error']}")
    return data


def _exceeded_limit(page: dict) -> bool:
    # esri JSON puts the flag at the top level; GeoJSON puts it under "properties".
    return bool(
        page.get("exceededTransferLimit")
        or page.get("properties", {}).get("exceededTransferLimit")
    )


def fetch_all(source: Source) -> list[dict]:
    """Fetch every record, paginating until the server reports no more.

    Returns esri `attributes` dicts for JSON sources, or GeoJSON features for
    GeoJSON sources.
    """
    records: list[dict] = []
    offset = 0
    while True:
        page = fetch_page(source, offset)
        if source.geojson:
            batch = page.get("features", [])
        else:
            batch = [f["attributes"] for f in page.get("features", [])]
        records.extend(batch)
        print(f"  {source.name}: fetched {len(records):,} records")
        if not batch or not _exceeded_limit(page):
            return records
        offset += len(batch)
