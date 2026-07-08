"""External system integrations."""

from src.integrations.crm import CRMClient, HubSpotClient
from src.integrations.secrets_vault import SecretsVault, get_secrets_vault, mask_secret
from src.integrations.webhooks import IntegrationRouter, WebhookDispatcher

__all__ = [
    "CRMClient",
    "HubSpotClient",
    "IntegrationRouter",
    "SecretsVault",
    "WebhookDispatcher",
    "get_secrets_vault",
    "mask_secret",
]
