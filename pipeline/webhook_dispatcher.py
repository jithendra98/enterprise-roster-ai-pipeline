import json
import requests
from typing import List, Dict, Any
from .models import ComplianceViolation

class WebhookAlertDispatcher:
    """
    Constructs formatted alert cards and dispatches automated incident
    notifications to enterprise communication channels (Slack / MS Teams).
    """

    def __init__(self, webhook_url: str = None):
        self.webhook_url = webhook_url

    def build_slack_payload(self, violations: List[ComplianceViolation]) -> Dict[str, Any]:
        critical_count = sum(1 for v in violations if v.severity == "CRITICAL")
        warning_count = sum(1 for v in violations if v.severity == "WARNING")

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "🚨 MoveInSync Commute Ops: Roster Discrepancy Alert"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Summary:* Identified *{len(violations)}* compliance item(s) requiring attention.\n• *Critical (Escort/Safety):* {critical_count}\n• *Warnings (Data/Geo):* {warning_count}"
                }
            },
            {"type": "divider"}
        ]

        for v in violations[:5]:  # sample top 5 in alert preview
            emoji = "🔴" if v.severity == "CRITICAL" else "🟡"
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"{emoji} *[{v.policy_code}]* *{v.employee_name}* (`{v.employee_id}`)\n{v.description}\n_Action:_ `{v.suggested_action}`"
                }
            })

        return {"blocks": blocks}

    def dispatch_violations(self, violations: List[ComplianceViolation], dry_run: bool = True) -> List[Dict[str, Any]]:
        if not violations:
            return []

        payload = self.build_slack_payload(violations)
        dispatches = []

        if dry_run or not self.webhook_url:
            dispatches.append({
                "status": "DRY_RUN_SIMULATION",
                "endpoint": self.webhook_url or "https://hooks.slack.com/services/SIMULATED/ENDPOINT",
                "payload": payload
            })
        else:
            try:
                response = requests.post(
                    self.webhook_url,
                    data=json.dumps(payload),
                    headers={"Content-Type": "application/json"},
                    timeout=5
                )
                dispatches.append({
                    "status": "SENT" if response.status_code == 200 else f"FAILED_{response.status_code}",
                    "endpoint": self.webhook_url,
                    "payload": payload
                })
            except Exception as e:
                dispatches.append({
                    "status": f"ERROR: {str(e)}",
                    "endpoint": self.webhook_url,
                    "payload": payload
                })

        return dispatches
