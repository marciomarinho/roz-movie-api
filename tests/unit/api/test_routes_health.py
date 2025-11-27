"""Unit tests for health check routes."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.api.routes_health import router


@pytest.fixture
def client():
    """Create a test client for health routes."""
    from fastapi import FastAPI
    
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


class TestHealthCheckRoute:
    """Test suite for health check endpoint."""

    def test_health_check_success(self, client):
        """Test successful health check."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

    def test_health_check_response_format(self, client):
        """Test health check response has correct format."""
        response = client.get("/health")
        
        assert isinstance(response.json(), dict)
        assert "status" in response.json()

    def test_health_check_no_authentication_required(self, client):
        """Test that health check doesn't require authentication."""
        # Health check should work without any headers
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_check_response_content_type(self, client):
        """Test health check response content type."""
        response = client.get("/health")
        
        assert "application/json" in response.headers.get("content-type", "")

    def test_health_check_multiple_calls(self, client):
        """Test multiple health check calls."""
        for _ in range(5):
            response = client.get("/health")
            assert response.status_code == 200
            assert response.json()["status"] == "ok"

    def test_health_check_with_accept_header(self, client):
        """Test health check with custom accept header."""
        response = client.get("/health", headers={"Accept": "application/json"})
        
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_health_check_method_not_allowed(self, client):
        """Test that POST is not allowed on health endpoint."""
        response = client.post("/health")
        
        # Should be 405 Method Not Allowed
        assert response.status_code == 405

    def test_health_check_put_not_allowed(self, client):
        """Test that PUT is not allowed on health endpoint."""
        response = client.put("/health")
        
        assert response.status_code == 405

    def test_health_check_delete_not_allowed(self, client):
        """Test that DELETE is not allowed on health endpoint."""
        response = client.delete("/health")
        
        assert response.status_code == 405
