"""MODEL: data shapes for live hotel search results.

These describe *places returned by Geoapify*, not bookable hotel rooms.
There is deliberately no price, rating, or availability field -- the
provider does not supply them and we never invent them.
"""
from typing import Optional

from pydantic import BaseModel


class SearchCenter(BaseModel):
    """The postcode location Geoapify returned for the requested ZIP."""
    zip: str                      # always a 5-char string, leading zeros kept
    lat: float
    lon: float
    label: Optional[str] = None   # provider's formatted label, e.g. "State College, PA 16801, United States"


class PlaceResult(BaseModel):
    """One hotel-category place from the Geoapify Places API."""
    provider: str = "geoapify"
    provider_place_id: str        # Geoapify place_id -- stable key for Part 2 shortlist
    name: Optional[str] = None    # None when the provider has no name; the view labels it honestly
    address: Optional[str] = None
    lat: float
    lon: float
    distance_m: Optional[int] = None  # straight-line distance from the search center


class SearchResponse(BaseModel):
    center: SearchCenter
    radius_m: int
    result_limit: int             # max results requested from the provider (not a full inventory)
    count: int
    hotels: list[PlaceResult]
