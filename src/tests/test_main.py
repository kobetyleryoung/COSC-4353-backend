"""
Tests for main FastAPI application
"""
import pytest
from fastapi.testclient import TestClient

from src.main import app


class TestMainApp:
    """Test main FastAPI application"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    def test_health_endpoint(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    def test_api_docs_available(self, client):
        """Test API documentation is available"""
        response = client.get("/docs")
        assert response.status_code == 200
    
    def test_redoc_available(self, client):
        """Test ReDoc documentation is available"""
        response = client.get("/redoc")
        assert response.status_code == 200
    
    def test_openapi_schema(self, client):
        """Test OpenAPI schema is available"""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "info" in data
        assert data["info"]["title"] == "Volunteer Management System"
        assert data["info"]["version"] == "1.0.0"
    
    def test_cors_headers(self, client):
        """Test CORS headers are present"""
        response = client.options("/health")
        assert response.status_code == 200