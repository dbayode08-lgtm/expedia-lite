"""CONTROLLER: HTTP endpoints for saved (local) hotels.

  GET    /api/local/hotels?zip=16801   saved hotels for a ZIP (+ dated demo nights)
  GET    /api/local/saved-ids          provider IDs of every saved hotel
  POST   /api/local/hotels             save an API hotel with its searched-ZIP context
  DELETE /api/local/hotels/{hotel_id}  remove a saved hotel and its related rows

A database failure returns 500 `local_storage_error` -- never an empty list --
so the frontend can tell "nothing saved" apart from "lookup failed".
"""
import sqlite3
from typing import Optional

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

import seed
from live_search.geoapify_client import SEARCH_RADIUS_M, is_valid_zip

from . import repository

router = APIRouter(prefix="/api/local", tags=["saved local hotels"])


def _error(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(status_code=status, content={"error": code, "message": message})


class HotelIn(BaseModel):
    provider_place_id: str = Field(min_length=1)
    name: Optional[str] = None
    address: Optional[str] = None
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    distance_m: Optional[int] = None


class CenterIn(BaseModel):
    zip: str
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    label: Optional[str] = None


class SaveRequest(BaseModel):
    hotel: HotelIn
    center: CenterIn


@router.get("/hotels")
def list_saved_for_zip(zip: str = Query(..., description="Five-digit U.S. ZIP")):
    zip_code = zip.strip()
    if not is_valid_zip(zip_code):
        return _error(400, "invalid_zip", "Enter exactly five digits, e.g. 16801 or 02134.")
    try:
        conn = seed.get_conn()
        try:
            center, hotels = repository.hotels_for_zip(conn, zip_code)
        finally:
            conn.close()
    except sqlite3.Error:
        return _error(500, "local_storage_error", "Couldn't read saved hotels from the local database.")
    return {
        "source": "local",
        "zip": zip_code,
        "center": center,
        "radius_m": SEARCH_RADIUS_M,
        "count": len(hotels),
        "hotels": hotels,
        "note": "Nightly rates and rooms are simulated classroom data, not hotel API data.",
    }


@router.get("/saved-ids")
def list_saved_ids():
    try:
        conn = seed.get_conn()
        try:
            ids = repository.saved_ids(conn)
        finally:
            conn.close()
    except sqlite3.Error:
        return _error(500, "local_storage_error", "Couldn't read saved hotels from the local database.")
    return {"ids": ids}


@router.post("/hotels", status_code=201)
def save_hotel(req: SaveRequest):
    if not is_valid_zip(req.center.zip):
        return _error(400, "invalid_zip", "The searched ZIP must be exactly five digits.")
    try:
        conn = seed.get_conn()
        try:
            created = repository.save_hotel(conn, req.hotel.model_dump(), req.center.model_dump())
        finally:
            conn.close()
    except sqlite3.Error:
        return _error(500, "local_storage_error", "Couldn't save the hotel to the local database.")
    return {"hotel_id": req.hotel.provider_place_id, "saved": True, "created": created}


@router.delete("/hotels/{hotel_id}")
def remove_hotel(hotel_id: str):
    try:
        conn = seed.get_conn()
        try:
            removed = repository.remove_hotel(conn, hotel_id)
        finally:
            conn.close()
    except sqlite3.Error:
        return _error(500, "local_storage_error", "Couldn't remove the hotel from the local database.")
    if not removed:
        return _error(404, "not_saved", "That hotel isn't saved locally.")
    return {"hotel_id": hotel_id, "removed": True}
