"""
LifeLens Ω - API Endpoints Integration Test Suite
Verifies all FastAPI routes (reality-check, payment-check, link-check, image-check, alternatives).
"""

import pytest
from fastapi.testclient import TestClient
from src.api.app import app

@pytest.fixture(scope="module")
def client():
    """Create a test client that triggers startup/shutdown event handlers."""
    with TestClient(app) as c:
        yield c


def test_health_check_endpoint(client):
    """Verify health endpoint response."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "version" in data


def test_reality_check_endpoint_legitimate(client):
    """Verify reality check endpoint returns low risk for safe messages."""
    payload = {
        "content": "Hey, how are you doing today?",
        "event_type": "message",
        "source_channel": "sms"
    }
    response = client.post("/api/v1/reality-check", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "assessment_id" in data
    assert data["integrity_score"] > 0.5
    assert data["risk_level"] in ["LOW", "MEDIUM"]


def test_reality_check_endpoint_phishing(client):
    """Verify reality check endpoint returns high risk for phishing attempts."""
    payload = {
        "content": "URGENT: Your bank account is compromised. Click here to verify immediately: http://fake-bank.fake/verify",
        "event_type": "message",
        "source_channel": "whatsapp"
    }
    response = client.post("/api/v1/reality-check", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "assessment_id" in data
    assert data["integrity_score"] < 0.5
    assert data["risk_level"] in ["HIGH", "CRITICAL"]


def test_payment_check_endpoint(client):
    """Verify payment check logic based on amount and recipient."""
    # Test low risk
    response = client.post("/api/v1/payment-check", json={
        "amount": 500.0,
        "recipient": "John Doe"
    })
    assert response.status_code == 200
    assert response.json()["risk_level"] == "LOW"

    # Test high risk
    response = client.post("/api/v1/payment-check", json={
        "amount": 75000.0,
        "recipient": "Unknown Vendor Support Agent"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["risk_level"] == "HIGH"
    assert data["reversibility"] == 0.15


def test_link_check_endpoint(client):
    """Verify link check classification."""
    # Safe link
    response = client.post("/api/v1/link-check", json={"url": "https://official-bank.com/dashboard"})
    assert response.status_code == 200
    assert response.json()["is_safe"] is True

    # Phishing link
    response = client.post("/api/v1/link-check", json={"url": "https://secure-login.fake-bank.fake/verify"})
    assert response.status_code == 200
    assert response.json()["is_safe"] is False
    assert response.json()["risk_level"] == "HIGH"


def test_image_check_endpoint(client):
    """Verify image metadata authenticity check."""
    # Normal image
    response = client.post("/api/v1/image-check", json={"image_url": "https://example.com/receipt.jpg"})
    assert response.status_code == 200
    assert response.json()["is_manipulated"] is False

    # Fake image
    response = client.post("/api/v1/image-check", json={"image_url": "https://example.com/fake-receipt-edited.jpg"})
    assert response.status_code == 200
    assert response.json()["is_manipulated"] is True
    assert response.json()["authenticity_score"] == 0.25


def test_alternatives_endpoint(client):
    """Verify generation of safe alternatives based on goal."""
    response = client.post("/api/v1/alternatives", json={
        "action_type": "payment",
        "goal": "Pay utility bill"
    })
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert data[0]["risk_level"] == "LOW"
    assert "official" in data[0]["description"].lower()
