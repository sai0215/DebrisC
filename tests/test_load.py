"""Smoke tests on the committed sample data."""

import pandas as pd
import pytest

from pipeline.ingest import assert_no_private_fields
from pipeline.load import geojson_properties, load_houston_dms, load_la_tickets
from pipeline.sources import HOUSTON_DMS, LA_TICKETS, SOURCES


@pytest.mark.parametrize("source", SOURCES.values(), ids=SOURCES.keys())
def test_keep_and_private_fields_do_not_overlap(source):
    assert not set(source.keep_fields) & set(source.private_fields)


def test_assert_no_private_fields_raises():
    with pytest.raises(ValueError):
        assert_no_private_fields(["Ticket", "Load_Monitor"], LA_TICKETS)


def test_la_sample_loads_without_private_fields():
    df = load_la_tickets(prefer_raw=False)
    assert len(df) > 0
    assert set(df.columns) == set(LA_TICKETS.keep_fields)
    assert isinstance(df["Load_Date"].dtype, pd.DatetimeTZDtype)


def test_houston_sample_loads_without_private_fields():
    sites = load_houston_dms(prefer_raw=False)
    props = geojson_properties(sites)
    assert len(props) > 0
    assert set(props.columns) <= set(HOUSTON_DMS.keep_fields)
    assert all(f["geometry"] for f in sites["features"])
