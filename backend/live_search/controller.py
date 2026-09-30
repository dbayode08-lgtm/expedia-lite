"""CONTROLLER: HTTP entry point for live hotel search.

Validates input, calls the Geoapify model/service, and maps every outcome
to a distinct status + error code so the view can show the right state:

  200  results (hotels may be an empty list = "no nearby hotels")
  400  invalid_zip       -- not exactly five digits
  404  zip_not_found     -- geocoding did not establish that U.S. ZIP
  429  rate_limited      -- Geoapify quota / rate limit
  502  provider_error    -- timeout, bad key, provider down, bad response
  503  not_configured    -- GEOAPIFY_API_KEY missing on the server
"""
import os
from typing import AsyncIterator, Optional

import httpx
from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse

from .models import SearchResponse
from .geoapify_client import (
    RESULT_LIMIT,
    SEARCH_RADIUS_M,
    GeoapifyClient,
    ProviderRateLimited,
    ProviderUnavailable,
    ZipNotResolved,
    is_valid_zip,
)

router = APIRouter(prefix="/api/live", tags=["live hotel search"])


def _error(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(status_code=status, content={"error": code, "message": message})


async def get_geoapify_client() -> AsyncIterator[Optional[GeoapifyClient]]:
    key = os.getenv("GEOAPIFY_API_KEY", "").strip()
    if not key:
        yield None
        return
    async with httpx.AsyncClient() as http:
        yield GeoapifyClient(key, http)


@router.get("/hotels", response_model=SearchResponse)
async def search_hotels(
    zip: str = Query(..., description="Five-digit U.S. ZIP code, leading zeros allowed"),
    client: Optional[GeoapifyClient] = Depends(get_geoapify_client),
):
    zip_code = zip.strip()
    if not is_valid_zip(zip_code):
        return _error(400, "invalid_zip", "Enter exactly five digits, e.g. 16801 or 02134.")
    if client is None:
        return _error(503, "not_configured", "Hotel search is not configured on the server.")

    try:
        center = await client.resolve_zip(zip_code)
        hotels = await client.hotels_near(center)
    except ZipNotResolved:
        return _error(404, "zip_not_found", f"Couldn't find U.S. ZIP code {zip_code}.")
    except ProviderRateLimited:
        return _error(429, "rate_limited", "The map data service is busy (rate limit). Try again in a minute.")
    except ProviderUnavailable:
        return _error(502, "provider_error", "The map data service couldn't be reached. This is not an empty search.")

    return SearchResponse(
        center=center,
        radius_m=SEARCH_RADIUS_M,
        result_limit=RESULT_LIMIT,
        count=len(hotels),
        hotels=hotels,
    )
