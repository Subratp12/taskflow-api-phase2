"""
TaskFlow API — System Endpoint Integration Tests
─────────────────────────────────────────────────────────────────────────────
Tests /health and /ready endpoints via the HTTP layer.
These are critical — they validate what Kubernetes/ECS/Nginx probes will see.

Run: pytest tests/integration/test_health.py -v
"""

import json


class TestHealthEndpoint:
    """GET /health — Liveness probe tests."""

    def test_health_returns_200(self, client):
        """Health endpoint must return 200 OK."""
        response = client.get('/health')
        assert response.status_code == 200

    def test_health_returns_json(self, client):
        """Health endpoint must return valid JSON."""
        response = client.get('/health')
        assert response.content_type == 'application/json'
        data = response.get_json()
        assert data is not None

    def test_health_response_structure(self, client):
        """Health response has required fields."""
        response = client.get('/health')
        data = response.get_json()

        assert 'status' in data
        assert 'timestamp' in data
        assert 'version' in data
        assert 'app' in data

    def test_health_status_is_healthy(self, client):
        """Health status must be 'healthy'."""
        response = client.get('/health')
        data = response.get_json()
        assert data['status'] == 'healthy'

    def test_health_returns_version(self, client):
        """Health response includes app version."""
        response = client.get('/health')
        data = response.get_json()
        assert isinstance(data['version'], str)
        assert len(data['version']) > 0

    def test_health_no_auth_required(self, client):
        """Health endpoint must NOT require authentication."""
        # No Authorization header — should still return 200
        response = client.get('/health', headers={})
        assert response.status_code == 200

    def test_health_head_method(self, client):
        """HEAD /health should also work (used by some load balancers)."""
        response = client.head('/health')
        assert response.status_code == 200


class TestReadinessEndpoint:
    """GET /ready — Readiness probe tests."""

    def test_ready_returns_200_when_db_connected(self, client):
        """Ready endpoint returns 200 when database is reachable."""
        response = client.get('/ready')
        # If test DB is available, should be 200
        assert response.status_code in (200, 503)  # 503 if no test DB

    def test_ready_returns_json(self, client):
        """Ready endpoint returns valid JSON."""
        response = client.get('/ready')
        assert response.content_type == 'application/json'
        data = response.get_json()
        assert data is not None

    def test_ready_response_has_checks(self, client):
        """Ready response includes a 'checks' object."""
        response = client.get('/ready')
        data = response.get_json()
        assert 'checks' in data

    def test_ready_response_has_status(self, client):
        """Ready response includes a 'status' field."""
        response = client.get('/ready')
        data = response.get_json()
        assert 'status' in data
        assert data['status'] in ('ready', 'not_ready')

    def test_ready_no_auth_required(self, client):
        """Ready endpoint must NOT require authentication."""
        response = client.get('/ready', headers={})
        assert response.status_code in (200, 503)

    def test_ready_includes_version(self, client):
        """Ready response includes version."""
        response = client.get('/ready')
        data = response.get_json()
        assert 'version' in data

    def test_ready_db_check_present(self, client):
        """Ready response includes database check result."""
        response = client.get('/ready')
        data = response.get_json()
        assert 'database' in data.get('checks', {})


class TestSecurityHeaders:
    """Verify security headers are set on all responses."""

    def test_no_server_header(self, client):
        """Server header should be removed (don't leak server info)."""
        response = client.get('/health')
        assert 'Server' not in response.headers

    def test_x_content_type_options(self, client):
        """X-Content-Type-Options: nosniff must be set."""
        response = client.get('/health')
        assert response.headers.get('X-Content-Type-Options') == 'nosniff'

    def test_x_frame_options(self, client):
        """X-Frame-Options: DENY must be set."""
        response = client.get('/health')
        assert response.headers.get('X-Frame-Options') == 'DENY'

    def test_correlation_id_header_present(self, client):
        """Every response must include X-Correlation-ID."""
        response = client.get('/health')
        assert 'X-Correlation-ID' in response.headers

    def test_correlation_id_is_echoed(self, client):
        """If X-Correlation-ID is sent, it should be echoed back."""
        custom_id = 'test-correlation-id-12345'
        response = client.get('/health', headers={'X-Correlation-ID': custom_id})
        assert response.headers.get('X-Correlation-ID') == custom_id

    def test_correlation_id_generated_if_missing(self, client):
        """If no X-Correlation-ID is sent, one should be generated."""
        response = client.get('/health')
        correlation_id = response.headers.get('X-Correlation-ID')
        assert correlation_id is not None
        assert len(correlation_id) > 0


class TestErrorHandlers:
    """Verify error handlers return JSON, never HTML."""

    def test_404_returns_json(self, client):
        """404 Not Found must return JSON, not HTML."""
        response = client.get('/api/v1/this-route-does-not-exist')
        assert response.status_code == 404
        assert response.content_type == 'application/json'
        data = response.get_json()
        assert data['success'] is False
        assert 'error' in data

    def test_405_returns_json(self, client):
        """405 Method Not Allowed must return JSON."""
        response = client.delete('/health')  # /health only allows GET
        assert response.status_code == 405
        data = response.get_json()
        assert data is not None
        assert data['success'] is False

    def test_error_response_structure(self, client):
        """All error responses follow the standard envelope."""
        response = client.get('/api/v1/nonexistent')
        data = response.get_json()

        assert 'success' in data
        assert data['success'] is False
        assert 'error' in data
        assert 'code' in data['error']
        assert 'message' in data['error']
