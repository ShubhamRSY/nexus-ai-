"""API tests for integrations credentials vault."""

import json
import uuid
from pathlib import Path

import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient

from src.integrations.secrets_vault import SecretsVault


def _register_admin(client: TestClient) -> dict[str, str]:
    """Return Authorization headers for a fresh admin user."""
    suffix = uuid.uuid4().hex[:8]
    reg = client.post(
        "/api/v1/auth/register",
        json={
            "email": f"integrations-admin-{suffix}@example.com",
            "password": "AdminPass123!",
            "name": "Integrations Admin",
        },
    )
    assert reg.status_code == 200, reg.text
    return {"Authorization": f"Bearer {reg.json()['token']}"}


@pytest.fixture
def vault_client(monkeypatch, tmp_path: Path):
    vault_path = tmp_path / "integrations.vault"
    key = Fernet.generate_key()
    vault = SecretsVault(path=vault_path, key=key)

    monkeypatch.setattr("src.integrations.secrets_vault.VAULT_FILE", vault_path)
    monkeypatch.setattr("src.integrations.secrets_vault.get_secrets_vault", lambda: vault)
    monkeypatch.setattr("src.integrations.secrets_vault.reload_secrets_vault", lambda: vault)
    monkeypatch.setattr("src.api.integration_routes.get_secrets_vault", lambda: vault)
    from src.config import reload_settings
    from src.main import app

    reload_settings()
    client = TestClient(app)
    client.admin_headers = _register_admin(client)
    return client


class TestIntegrationsAPI:
    def test_status_shows_unconfigured_providers(self, vault_client: TestClient):
        res = vault_client.get("/api/v1/integrations/status")
        assert res.status_code == 200
        body = res.json()
        assert body["providers"]["openai"]["configured"] is False
        assert body["mock_mode"] is True

    def test_save_and_read_credentials(self, vault_client: TestClient):
        res = vault_client.put(
            "/api/v1/integrations/credentials",
            json={"openai_api_key": "sk-ui-saved-key-12345678"},
            headers=vault_client.admin_headers,
        )
        assert res.status_code == 200
        assert res.json()["providers"]["openai"]["configured"] is True

        status = vault_client.get("/api/v1/integrations/status").json()
        assert status["providers"]["openai"]["source"] == "vault"
        assert "sk-u" in status["providers"]["openai"]["masked_key"]
        assert "sk-ui-saved-key" not in json.dumps(status)

    def test_register_webhook_persists(self, vault_client: TestClient):
        res = vault_client.post(
            "/api/v1/integrations/webhooks",
            json={
                "event_type": "conversation.started",
                "url": "https://hooks.zapier.com/hooks/catch/test/123",
            },
            headers=vault_client.admin_headers,
        )
        assert res.status_code == 200

        status = vault_client.get("/api/v1/integrations/status").json()
        assert status["providers"]["ipaas"]["configured"] is True
        assert status["providers"]["ipaas"]["events"]["conversation.started"]["configured"] is True

    def test_settings_token_required_when_configured(self, vault_client: TestClient, monkeypatch):
        monkeypatch.setenv("SETTINGS_ADMIN_TOKEN", "secret-admin-token")
        from src.config import reload_settings

        reload_settings()

        res = vault_client.put(
            "/api/v1/integrations/credentials",
            json={"hubspot_api_key": "pat-test"},
        )
        assert res.status_code == 401

        res = vault_client.put(
            "/api/v1/integrations/credentials",
            json={"hubspot_api_key": "pat-test"},
            headers={"X-Settings-Token": "secret-admin-token"},
        )
        assert res.status_code == 401

        res = vault_client.put(
            "/api/v1/integrations/credentials",
            json={"hubspot_api_key": "pat-test"},
            headers=vault_client.admin_headers,
        )
        assert res.status_code == 401

        res = vault_client.put(
            "/api/v1/integrations/credentials",
            json={"hubspot_api_key": "pat-test"},
            headers={
                **vault_client.admin_headers,
                "X-Settings-Token": "secret-admin-token",
            },
        )
        assert res.status_code == 200
