import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_get_scrape_presets():
    response = client.get("/api/scrape/presets")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 3
    preset_ids = [item["id"] for item in data]
    assert "amazon_atta" in preset_ids
    assert "amazon_oil_violation" in preset_ids


def test_audit_listing_preset_compliant():
    response = client.post(
        "/api/scrape/listing",
        json={"url": "https://www.amazon.in/dp/B00V4J77A0", "preset_id": "amazon_atta"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["overall_tier"] == "likely_compliant"
    assert data["brand"] == "Aashirvaad"
    assert data["mrp"] == 275.0
    assert len(data["findings"]) >= 3


def test_audit_listing_preset_violation():
    response = client.post(
        "/api/scrape/listing",
        json={"url": "https://www.amazon.in/dp/B07XYZ9999", "preset_id": "amazon_oil_violation"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["overall_tier"] == "likely_violation"
    assert data["selling_price"] > data["mrp"]
    assert data["notice_draft"] is not None
    assert "Rule 6(10)" in data["notice_draft"]


def test_audit_listing_invalid_url():
    response = client.post(
        "/api/scrape/listing",
        json={"url": "ftp://invalid-url"}
    )
    assert response.status_code == 400
