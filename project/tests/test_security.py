"""Tests for production security hardening."""

import pytest
from fastapi.testclient import TestClient
from twilio.request_validator import RequestValidator


class TestDemoMode:
    def test_demo_reset_disabled_without_demo_mode(self, client, monkeypatch):
        monkeypatch.setenv("DEMO_MODE", "false")
        from src.config import reload_settings

        reload_settings()
        res = client.post("/api/v1/demo/reset")
        assert res.status_code == 404

    def test_demo_reset_enabled_in_dev(self, client):
        res = client.post("/api/v1/demo/reset")
        assert res.status_code == 200
        assert res.json()["status"] == "demo_reset"


class TestProductionDocs:
    def test_openapi_disabled_in_production(self, monkeypatch):
        monkeypatch.setenv("APP_ENV", "production")
        monkeypatch.setenv("DEMO_MODE", "false")
        from src.config import reload_settings

        reload_settings()
        import importlib
        import src.main

        importlib.reload(src.main)

        with TestClient(src.main.app) as prod_client:
            assert prod_client.get("/openapi.json").status_code == 404
            assert prod_client.get("/docs").status_code == 404

    def test_demo_reset_disabled_in_production(self, monkeypatch):
        monkeypatch.setenv("APP_ENV", "production")
        monkeypatch.setenv("DEMO_MODE", "true")
        from src.config import reload_settings

        reload_settings()
        import importlib
        import src.main

        importlib.reload(src.main)

        with TestClient(src.main.app) as prod_client:
            res = prod_client.post("/api/v1/demo/reset")
            assert res.status_code == 404


class TestTwilioSignature:
    def test_rejects_missing_signature_when_token_configured(self, client, monkeypatch):
        monkeypatch.setenv("TWILIO_AUTH_TOKEN", "test-auth-token")
        monkeypatch.setenv("TWILIO_WEBHOOK_BASE_URL", "http://testserver")
        from src.config import reload_settings

        reload_settings()
        res = client.post(
            "/api/v1/telephony/voice/inbound",
            data={"CallSid": "CA1", "From": "+15551234567"},
        )
        assert res.status_code == 403

    def test_accepts_valid_signature(self, client, monkeypatch):
        auth_token = "test-auth-token"
        monkeypatch.setenv("TWILIO_AUTH_TOKEN", auth_token)
        monkeypatch.setenv("TWILIO_WEBHOOK_BASE_URL", "http://testserver")
        from src.config import reload_settings

        reload_settings()

        params = {"CallSid": "CA1", "From": "+15551234567"}
        url = "http://testserver/api/v1/telephony/voice/inbound"
        signature = RequestValidator(auth_token).compute_signature(url, params)

        res = client.post(
            "/api/v1/telephony/voice/inbound",
            data=params,
            headers={"X-Twilio-Signature": signature},
        )
        assert res.status_code == 200


class TestWebSocketAuth:
    def test_websocket_rejects_without_token_when_auth_required(self, monkeypatch):
        monkeypatch.setenv("AUTH_REQUIRED", "true")
        monkeypatch.setenv("JWT_SECRET", "test-secret-for-ws-auth-tests-only")
        from src.config import reload_settings

        reload_settings()
        import importlib
        import src.main

        importlib.reload(src.main)

        with TestClient(src.main.app) as authed_client:
            with pytest.raises(Exception):
                with authed_client.websocket_connect("/api/v1/chat/stream"):
                    pass

    def test_websocket_accepts_valid_token(self, monkeypatch):
        monkeypatch.setenv("AUTH_REQUIRED", "true")
        monkeypatch.setenv("JWT_SECRET", "test-secret-for-ws-auth-tests-only")
        from src.auth import create_jwt
        from src.config import reload_settings

        reload_settings()
        import importlib
        import src.main

        importlib.reload(src.main)

        token = create_jwt({
            "sub": "user-1",
            "tenant_id": "t1",
            "email": "u@example.com",
            "name": "User",
            "role": "agent",
        })

        with TestClient(src.main.app) as authed_client:
            with authed_client.websocket_connect(f"/api/v1/chat/stream?token={token}") as ws:
                ws.send_json({"message": "Hello", "agent_id": "chat_support"})
                events = []
                import time
                deadline = time.time() + 25
                while time.time() < deadline:
                    try:
                        data = ws.receive_json()
                        events.append(data)
                        if data.get("type") in ("done", "error"):
                            break
                    except Exception:
                        break
                assert events, "no events received over WebSocket"
                assert any(e.get("type") == "done" for e in events), events
