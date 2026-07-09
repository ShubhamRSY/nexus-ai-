"""Execute saved workflow rules when CX events fire."""

from __future__ import annotations

import structlog

from src.database import db
from src.integrations.webhooks import IntegrationRouter

logger = structlog.get_logger()


async def run_workflows(tenant_id: str, trigger_event: str, context: dict | None = None) -> list[dict]:
    context = context or {}
    results: list[dict] = []
    router = IntegrationRouter()

    for rule in db.list_workflows(tenant_id):
        if rule.get("trigger_event") != trigger_event:
            continue
        if rule.get("enabled") is not None and not rule.get("enabled"):
            continue
        conditions = rule.get("conditions") or {}
        if conditions.get("channel") and context.get("channel") != conditions.get("channel"):
            continue

        for action in rule.get("actions") or []:
            atype = action.get("type", "")
            if atype == "send_webhook" and action.get("url"):
                await router.dispatcher.dispatch(action["url"], trigger_event, {**context, "rule": rule["name"]})
                results.append({"rule": rule["name"], "action": "webhook", "status": "sent"})
            elif atype == "escalate" and context.get("session_id"):
                db.escalate_session(context["session_id"], f"Workflow: {rule['name']}")
                await router.on_escalation(context["session_id"], rule["name"])
                results.append({"rule": rule["name"], "action": "escalate", "status": "done"})
            elif atype == "create_ticket":
                ticket = db.create_ticket(
                    tenant_id,
                    action.get("subject", f"Workflow: {rule['name']}"),
                    str(context),
                    session_id=context.get("session_id", ""),
                )
                await router.on_ticket_created(ticket)
                results.append({"rule": rule["name"], "action": "create_ticket", "status": "done"})
            elif atype == "notify_slack":
                from src.integrations.slack import SlackNotifier
                await SlackNotifier().send_alert("cx-alerts", f"[{rule['name']}] {trigger_event}: {context}")
                results.append({"rule": rule["name"], "action": "slack", "status": "sent"})

    if results:
        logger.info("workflows_executed", trigger=trigger_event, count=len(results))
    return results
