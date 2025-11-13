"""
Integration tests for webhook end-to-end flows.
"""

import pytest
from fastapi.testclient import TestClient
from backend.app import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


class TestWebhookFlows:
    """Test end-to-end webhook flows."""
    
    def test_health_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "checks" in data
    
    def test_echo_endpoint(self, client):
        """Test echo endpoint."""
        payload = {
            "event_type": "test",
            "data": {"test": "data"}
        }
        response = client.post("/echo", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
    
    def test_metrics_endpoint(self, client):
        """Test performance metrics endpoint."""
        response = client.get("/metrics")
        assert response.status_code == 200
        data = response.json()
        assert "metrics" in data
        assert "p50" in data["metrics"]
        assert "p95" in data["metrics"]
        assert "p99" in data["metrics"]

