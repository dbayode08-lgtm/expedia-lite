"""Offline checks for the search controller -- no live Geoapify calls.

Run from backend/:  python -m pytest -q
Each test fakes Geoapify with httpx.MockTransport so we can simulate
unresolved ZIPs, empty results, failures and rate limits without
spending quota.
"""
import httpx
import pytest
from fastapi.testclient import TestClient

from fastapi import FastAPI

from live_search.controller import get_geoapify_client, router
from live_search.geoapify_client import GEOCODE_URL, PLACES_URL, GeoapifyClient

# Mount only the live-search router: these checks never touch expedia_lite.db.
app = FastAPI()
app.include_router(router)

GEOCODE_16801 = {"results": [{
    "postcode": "16801", "country_code": "us", "result_type": "postcode",
    "lat": 40.7934, "lon": -77.86, "formatted": "State College, PA 16801, United States of America",
}]}

GEOCODE_02134 = {"results": [{
    "postcode": "02134", "country_code": "us", "result_type": "postcode",
    "lat": 42.3572, "lon": -71.1294, "formatted": "Boston, MA 02134, United States of America",
}]}

PLACES_TWO = {"type": "FeatureCollection", "features": [
    {"type": "Feature", "geometry": {"type": "Point", "coordinates": [-77.855, 40.795]},
     "properties": {"place_id": "far-one", "name": "Hotel Far", "lat": 40.81, "lon": -77.85,
                    "formatted": "1 Far St, State College, PA"}},
    {"type": "Feature", "geometry": {"type": "Point", "coordinates": [-77.861, 40.794]},
     "properties": {"place_id": "near-one", "lat": 40.794, "lon": -77.861}},   # no name, no address
    {"type": "Feature", "geometry": {"type": "Point", "coordinates": [-77.861, 40.794]},
     "properties": {"place_id": "near-one", "lat": 40.794, "lon": -77.861}},   # duplicate id
    {"type": "Feature", "geometry": {"type": "Point", "coordinates": []},
     "properties": {"name": "No id, skipped"}},
]}


def make_client(handler):
    def override():
        http = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        yield GeoapifyClient("test-key", http)
    app.dependency_overrides[get_geoapify_client] = override
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_overrides():
    yield
    app.dependency_overrides.clear()


def route(geocode=None, places=None, geocode_status=200, places_status=200):
    calls = []

    def handler(request: httpx.Request):
        calls.append(request)
        url = str(request.url)
        if url.startswith(GEOCODE_URL):
            return httpx.Response(geocode_status, json=geocode or {"results": []})
        if url.startswith(PLACES_URL):
            return httpx.Response(places_status, json=places or {"features": []})
        return httpx.Response(404)
    handler.calls = calls
    return handler


def test_results_normalized_sorted_deduped():
    c = make_client(route(GEOCODE_16801, PLACES_TWO))
    r = c.get("/api/live/hotels", params={"zip": "16801"})
    assert r.status_code == 200
    body = r.json()
    assert body["center"]["zip"] == "16801"
    assert body["radius_m"] == 5000
    ids = [h["provider_place_id"] for h in body["hotels"]]
    assert ids == ["near-one", "far-one"]           # nearest first, duplicate dropped, id-less skipped
    assert body["count"] == 2
    unnamed = body["hotels"][0]
    assert unnamed["name"] is None and unnamed["address"] is None
    for h in body["hotels"]:
        assert not {"price", "rating", "availability"} & h.keys()


def test_leading_zero_zip_kept_as_string():
    h = route(GEOCODE_02134, {"features": []})
    c = make_client(h)
    r = c.get("/api/live/hotels", params={"zip": "02134"})
    assert r.status_code == 200
    assert r.json()["center"]["zip"] == "02134"
    assert h.calls[0].url.params["postcode"] == "02134"
    assert h.calls[0].url.params["filter"] == "countrycode:us"


@pytest.mark.parametrize("bad", ["1680", "168011", "16a01", "", "  ", "16801-1234"])
def test_invalid_zip_rejected_without_calling_provider(bad):
    h = route(GEOCODE_16801, PLACES_TWO)
    c = make_client(h)
    r = c.get("/api/live/hotels", params={"zip": bad})
    assert r.status_code == 400 and r.json()["error"] == "invalid_zip"
    assert h.calls == []


def test_unresolved_zip_when_no_results():
    c = make_client(route({"results": []}))
    r = c.get("/api/live/hotels", params={"zip": "00000"})
    assert r.status_code == 404 and r.json()["error"] == "zip_not_found"


def test_different_postcode_is_not_accepted():
    # Provider "helpfully" returns a nearby but different ZIP -> must not search there.
    wrong = {"results": [{**GEOCODE_16801["results"][0], "postcode": "16803"}]}
    h = route(wrong, PLACES_TWO)
    c = make_client(h)
    r = c.get("/api/live/hotels", params={"zip": "16801"})
    assert r.status_code == 404
    assert not any(str(x.url).startswith(PLACES_URL) for x in h.calls)


def test_non_us_result_is_not_accepted():
    foreign = {"results": [{**GEOCODE_16801["results"][0], "country_code": "de"}]}
    c = make_client(route(foreign, PLACES_TWO))
    assert c.get("/api/live/hotels", params={"zip": "16801"}).status_code == 404


def test_empty_successful_search():
    c = make_client(route(GEOCODE_16801, {"type": "FeatureCollection", "features": []}))
    r = c.get("/api/live/hotels", params={"zip": "16801"})
    assert r.status_code == 200 and r.json()["count"] == 0 and r.json()["hotels"] == []


def test_rate_limit_is_distinct_from_empty():
    c = make_client(route(GEOCODE_16801, places_status=429))
    r = c.get("/api/live/hotels", params={"zip": "16801"})
    assert r.status_code == 429 and r.json()["error"] == "rate_limited"


@pytest.mark.parametrize("status", [401, 500, 503])
def test_provider_failure_is_distinct_from_empty(status):
    c = make_client(route(geocode_status=status))
    r = c.get("/api/live/hotels", params={"zip": "16801"})
    assert r.status_code == 502 and r.json()["error"] == "provider_error"
    assert "test-key" not in r.text   # key never leaks into responses


def test_network_timeout_is_provider_error():
    def boom(request):
        raise httpx.ConnectTimeout("timed out")
    c = make_client(boom)
    r = c.get("/api/live/hotels", params={"zip": "16801"})
    assert r.status_code == 502


def test_missing_key_reports_not_configured(monkeypatch):
    monkeypatch.delenv("GEOAPIFY_API_KEY", raising=False)
    r = TestClient(app).get("/api/live/hotels", params={"zip": "16801"})
    assert r.status_code == 503 and r.json()["error"] == "not_configured"
