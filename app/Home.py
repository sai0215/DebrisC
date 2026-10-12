"""Starter Streamlit page: loads both datasets and shows a few simple views.

Run from the project root:
    streamlit run app/Home.py
"""

import sys
from pathlib import Path

# Make `pipeline` importable when Streamlit runs this file directly.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
import plotly.express as px
import pydeck as pdk
import streamlit as st

from pipeline.load import geojson_properties, load_houston_dms, load_la_tickets

MAP_POINTS = 3_000  # points drawn on the map, sampled for speed
BAR_COLOR = "#2a78d6"

st.set_page_config(page_title="Debris Data Explorer", layout="wide")


@st.cache_data
def get_la(prefer_raw: bool) -> pd.DataFrame:
    return load_la_tickets(prefer_raw)


@st.cache_data
def get_houston(prefer_raw: bool) -> dict:
    return load_houston_dms(prefer_raw)


st.title("Debris Data Explorer")
prefer_raw = st.sidebar.toggle(
    "Use full data (data/raw) if available",
    value=True,
    help="Off = use the small committed sample in data/sample/.",
)

la_tab, houston_tab = st.tabs(["Louisiana load tickets (Laura 2020)", "Houston DMS sites"])

with la_tab:
    la = get_la(prefer_raw)

    parishes = sorted(la["Parish"].dropna().unique())
    selected = st.multiselect("Parish", parishes, placeholder="All parishes")
    if selected:
        la = la[la["Parish"].isin(selected)]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Loads", f"{len(la):,}")
    c2.metric("Cubic yards hauled", f"{la['Haul_Vol'].sum():,.0f}")
    c3.metric("Trucks", f"{la['Truck'].nunique():,}")
    c4.metric(
        "Date range",
        f"{la['Load_Date'].min():%b %d} – {la['Load_Date'].max():%b %d, %Y}" if len(la) else "—",
    )

    daily = (
        la.groupby(la["Load_Date"].dt.date)["Haul_Vol"].sum()
        .rename_axis("Day").reset_index(name="Cubic yards")
    )
    fig = px.bar(daily, x="Day", y="Cubic yards", title="Cubic yards hauled per day")
    fig.update_traces(marker_color=BAR_COLOR)
    st.plotly_chart(fig, width="stretch")

    left, right = st.columns(2)
    for col, field in ((left, "Disposal_Site"), (right, "Pay_Item")):
        by = la.groupby(field)["Haul_Vol"].sum().sort_values().tail(10).reset_index()
        fig = px.bar(by, x="Haul_Vol", y=field, orientation="h",
                     title=f"Top 10 by {field} (CY)", labels={"Haul_Vol": "Cubic yards"})
        fig.update_traces(marker_color=BAR_COLOR)
        col.plotly_chart(fig, width="stretch")

    st.subheader("Load locations")
    points = la.dropna(subset=["Begin_Lat", "Begin_Long"])
    st.caption(f"Showing {min(MAP_POINTS, len(points)):,} of {len(points):,} loads (random sample).")
    st.map(points.sample(min(MAP_POINTS, len(points)), random_state=0),
           latitude="Begin_Lat", longitude="Begin_Long", size=30)

    with st.expander("Raw rows"):
        st.dataframe(la.head(500), width="stretch")

with houston_tab:
    sites = get_houston(prefer_raw)
    props = geojson_properties(sites)

    st.metric("Sites", len(props))
    layer = pdk.Layer(
        "GeoJsonLayer",
        data=sites,
        pickable=True,
        stroked=True,
        filled=True,
        get_fill_color=[42, 120, 214, 120],
        get_line_color=[20, 60, 120],
        line_width_min_pixels=2,
    )
    view = pdk.ViewState(latitude=29.76, longitude=-95.37, zoom=9.5)
    st.pydeck_chart(pdk.Deck(
        layers=[layer],
        initial_view_state=view,
        tooltip={"text": "{SiteName}\nsize {PropertySize} · {StormName} {YearUsed}"},
    ))
    st.dataframe(props, width="stretch", hide_index=True)
