"""
Tests for main.py helper functions.
"""
import json
import pytest
from unittest.mock import MagicMock, patch
from aiohttp.test_utils import make_mocked_request

from main import health_check_handler, create_healthcheck_server


class TestHealthCheckHandler:
    """Tests for health_check_handler function."""
    
    @pytest.mark.asyncio
    async def test_health_check_handler_returns_correct_json(self):
        """Test returning correct JSON response."""
        mock_request = MagicMock()
        
        response = await health_check_handler(mock_request)
        
        # Response should be aiohttp web.Response
        assert hasattr(response, 'status')
        assert response.status == 200
        
        # Parse JSON body - aiohttp Response has text property, need to parse JSON
        import json
        body = json.loads(response.text)
        assert body["status"] == "healthy"
        assert body["service"] == "game-allocator-service"
    
    @pytest.mark.asyncio
    async def test_health_check_handler_uses_service_name(self):
        """Test using SERVICE_NAME from settings."""
        mock_request = MagicMock()
        
        response = await health_check_handler(mock_request)
        # aiohttp Response has text property, need to parse JSON
        import json
        body = json.loads(response.text)
        
        assert body["service"] == "game-allocator-service"


class TestCreateHealthcheckServer:
    """Tests for create_healthcheck_server function."""
    
    def test_create_healthcheck_server_creates_app(self):
        """Test creating aiohttp Application."""
        app = create_healthcheck_server()
        
        assert app is not None
        assert hasattr(app, 'router')
    
    def test_create_healthcheck_server_registers_health_endpoint(self):
        """Test registration of /health endpoint."""
        app = create_healthcheck_server()
        
        # Get all routes - check resource if available
        routes = []
        for route in app.router.routes():
            if hasattr(route, 'resource'):
                resource = route.resource
                if hasattr(resource, 'canonical'):
                    routes.append(resource.canonical)
                elif hasattr(resource, '_path'):
                    routes.append(resource._path)
            elif hasattr(route, 'path'):
                routes.append(route.path)
            elif hasattr(route, '_path'):
                routes.append(route._path)
        
        route_strings = [str(route) for route in routes]
        assert any("/health" in route_str for route_str in route_strings)

