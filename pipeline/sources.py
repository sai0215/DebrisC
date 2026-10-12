"""Source definitions: where each dataset lives and which fields we keep.

PRIVACY: only fields listed in `keep_fields` are requested from the server, so
personal fields never reach disk. `private_fields` is a second safety net that
ingest checks before saving. Do not add any private field to `keep_fields`.
"""

from dataclasses import dataclass
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
RAW_DIR = DATA_DIR / "raw"
SAMPLE_DIR = DATA_DIR / "sample"


@dataclass(frozen=True)
class Source:
    """An ArcGIS REST layer and how to store it locally."""

    name: str
    url: str
    keep_fields: tuple[str, ...]
    private_fields: tuple[str, ...]
    filename: str
    geojson: bool = False  # True: request f=geojson with geometry (polygons)
    page_size: int = 10_000


LA_TICKETS = Source(
    name="la_tickets",
    url="https://maps.dotd.la.gov/road/rest/services/DebrisTicketing/MapServer/0/query",
    keep_fields=(
        "OBJECTID", "Ticket", "Load_Date", "Disposal_Date", "Parish", "RouteName",
        "District", "Disposal_Site", "Capacity_L", "Haul_Vol", "Truck",
        "Contractor", "Pay_Item", "Pass", "Begin_Lat", "Begin_Long",
    ),
    private_fields=("Load_Monitor", "Disposal_Monitor"),
    filename="la_tickets.parquet",
)

HOUSTON_DMS = Source(
    name="houston_dms",
    url=(
        "https://services.arcgis.com/NummVBqZSIJKUeVR/ArcGIS/rest/services/"
        "DMS_Sites_view_layer/FeatureServer/0/query"
    ),
    keep_fields=(
        "OBJECTID", "SiteName", "PropertySize", "City", "State", "YearUsed", "StormName",
    ),
    private_fields=(
        "Owner", "OwnerFullAddress", "OwnerPhone", "OwnerEmail",
        "created_user", "last_edited_user",
    ),
    filename="houston_dms.geojson",
    geojson=True,
    page_size=2_000,
)

SOURCES: dict[str, Source] = {s.name: s for s in (LA_TICKETS, HOUSTON_DMS)}
