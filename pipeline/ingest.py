"""Pull a source from ArcGIS and save it locally.

Usage:
    python -m pipeline.ingest --source la_tickets            # full pull -> data/raw/
    python -m pipeline.ingest --source la_tickets --sample   # also writes 5k-row sample -> data/sample/
    python -m pipeline.ingest --source houston_dms --sample
"""

import argparse
import json
from pathlib import Path

import pandas as pd

from pipeline.arcgis import fetch_all
from pipeline.sources import RAW_DIR, SAMPLE_DIR, SOURCES, Source

SAMPLE_ROWS = 5_000
SAMPLE_SEED = 42


def assert_no_private_fields(columns: list[str], source: Source) -> None:
    """Fail loudly if any personal field is about to be saved."""
    leaked = set(columns) & set(source.private_fields)
    if leaked:
        raise ValueError(f"Private fields present in {source.name}: {sorted(leaked)}")


def save_tabular(records: list[dict], source: Source, sample: bool) -> None:
    """Save attribute records as Parquet (full to raw/, optional random sample to sample/)."""
    df = pd.DataFrame.from_records(records)
    assert_no_private_fields(list(df.columns), source)
    _write_parquet(df, RAW_DIR / source.filename)
    if sample:
        n = min(SAMPLE_ROWS, len(df))
        _write_parquet(df.sample(n=n, random_state=SAMPLE_SEED), SAMPLE_DIR / source.filename)


def save_geojson(features: list[dict], source: Source, sample: bool) -> None:
    """Save GeoJSON features (small datasets: the sample is the full set)."""
    for feat in features:
        assert_no_private_fields(list(feat.get("properties", {})), source)
    collection = {"type": "FeatureCollection", "features": features}
    _write_json(collection, RAW_DIR / source.filename)
    if sample:
        _write_json(collection, SAMPLE_DIR / source.filename)


def _write_parquet(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)
    print(f"  wrote {len(df):,} rows -> {path}")


def _write_json(obj: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj))
    print(f"  wrote {len(obj['features']):,} features -> {path}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--source", required=True, choices=sorted(SOURCES))
    parser.add_argument("--sample", action="store_true", help="also write a small sample to data/sample/")
    args = parser.parse_args()

    source = SOURCES[args.source]
    print(f"Ingesting {source.name} ...")
    records = fetch_all(source)
    if source.geojson:
        save_geojson(records, source, args.sample)
    else:
        save_tabular(records, source, args.sample)


if __name__ == "__main__":
    main()
