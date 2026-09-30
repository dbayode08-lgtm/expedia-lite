"""MODEL (data access): talks to Geoapify and normalizes its responses.

Only the backend ever sees GEOAPIFY_API_KEY. The frontend calls our own
/api/hotels/search endpoint and never talks to Geoapify directly.
"""
import math
import re
from typing import Any, Optional

import httpx

from .models import PlaceResult, SearchCenter

GEOCODE_URL = "https://api.geoapify.com/v1/geocode/search"
PLACES_URL = "https://api.geoapify.com/v2/places"

HOTEL_CATEGORY = "accommodation.hotel"
SEARCH_RADIUS_M = 5000
RESULT_LIMIT = 50           # provider max per request we ask for; documented as a limit, not an inventory
TIMEOUT_S = 10.0

ZIP_RE = re.compile(r"^\d{5}$")


# ---- Errors the controller maps to distinct HTTP responses / UI states ----
class GeoapifyError(Exception):
    """Base class for provider problems."""


class ZipNotResolved(GeoapifyError):
    """Geocoding did not return the requested U.S. ZIP code."""


class ProviderRateLimited(GeoapifyError):
    """Geoapify answered 429 (quota / rate limit)."""


class ProviderUnavailable(GeoapifyError):
    """Timeout, network failure, bad key, 5xx, or unreadable response."""


def is_valid_zip(zip_code: str) -> bool:
    return bool(ZIP_RE.match(zip_code or ""))


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> int:
    r = 6_371_000
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return round(2 * r * math.asin(math.sqrt(a)))


class GeoapifyClient:
    def __init__(self, api_key: str, http: httpx.AsyncClient):
        self.api_key = api_key
        self.http = http

    async def _get(self, url: str, params: dict[str, Any]) -> dict:
        try:
            resp = await self.http.get(url, params={**params, "apiKey": self.api_key}, timeout=TIMEOUT_S)
        except httpx.HTTPError as exc:  # timeouts, DNS, connection resets
            raise ProviderUnavailable(f"network error: {type(exc).__name__}") from exc

        if resp.status_code == 429:
            raise ProviderRateLimited("Geoapify rate limit or quota reached")
        if resp.status_code >= 400:
            # 401/403 = bad key, 5xx = provider down. Never echo the URL (it contains the key).
            raise ProviderUnavailable(f"Geoapify HTTP {resp.status_code}")
        try:
            return resp.json()
        except ValueError as exc:
            raise ProviderUnavailable("unreadable Geoapify response") from exc

    async def resolve_zip(self, zip_code: str) -> SearchCenter:
        """Resolve a 5-digit ZIP to a U.S. postcode point.

        Accepts ONLY a result that is a U.S. postcode whose value matches the
        requested ZIP. Anything else (a city, a Canadian postcode, a different
        ZIP) raises ZipNotResolved instead of silently searching elsewhere.
        """
        data = await self._get(GEOCODE_URL, {
            "postcode": zip_code,
            "type": "postcode",
            "filter": "countrycode:us",
            "format": "json",
            "limit": 5,
        })
        results = data.get("results")
        if not isinstance(results, list):
            raise ProviderUnavailable("unexpected geocoding response shape")

        for r in results:
            postcode = str(r.get("postcode") or "")[:5]
            country = str(r.get("country_code") or "").lower()
            if postcode == zip_code and country == "us" and r.get("lat") is not None and r.get("lon") is not None:
                return SearchCenter(zip=zip_code, lat=float(r["lat"]), lon=float(r["lon"]),
                                    label=r.get("formatted"))
        raise ZipNotResolved(zip_code)

    async def hotels_near(self, center: SearchCenter) -> list[PlaceResult]:
        data = await self._get(PLACES_URL, {
            "categories": HOTEL_CATEGORY,
            "filter": f"circle:{center.lon},{center.lat},{SEARCH_RADIUS_M}",
            "bias": f"proximity:{center.lon},{center.lat}",
            "limit": RESULT_LIMIT,
        })
        features = data.get("features")
        if not isinstance(features, list):
            raise ProviderUnavailable("unexpected places response shape")

        hotels: dict[str, PlaceResult] = {}
        for f in features:
            place = normalize_feature(f, center)
            if place and place.provider_place_id not in hotels:
                hotels[place.provider_place_id] = place
        return sorted(hotels.values(), key=lambda h: (h.distance_m is None, h.distance_m or 0))


def normalize_feature(feature: dict, center: SearchCenter) -> Optional[PlaceResult]:
    """Map one GeoJSON feature to PlaceResult. Skip it if it has no id or coordinates."""
    props = feature.get("properties") or {}
    coords = (feature.get("geometry") or {}).get("coordinates") or []
    lon = props.get("lon", coords[0] if len(coords) >= 2 else None)
    lat = props.get("lat", coords[1] if len(coords) >= 2 else None)
    place_id = props.get("place_id")
    if not place_id or lat is None or lon is None:
        return None

    name = (props.get("name") or "").strip() or None
    address = props.get("formatted") or props.get("address_line2") or None
    lat, lon = float(lat), float(lon)
    return PlaceResult(
        provider_place_id=str(place_id),
        name=name,
        address=address,
        lat=lat,
        lon=lon,
        distance_m=haversine_m(center.lat, center.lon, lat, lon),
    )
