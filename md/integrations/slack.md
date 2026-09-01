# Integrations — Slack & ChatOps Connectors

## Status
**Status:** ✅ IMPLEMENTED (Incoming Webhooks & Block Kit Notification Cards)

---

## 1. Slack ChatOps Capabilities

* **Interactive Approval Notifications:** Posts structured Block Kit cards to dedicated Slack channels (`#finance-approvals`, `#it-incidents`) with direct deep-links to the Next.js approval portal.
* **Workflow Status Broadcasts:** Broadcasts real-time alerts when large batch ingestion jobs finish or when anomalies are detected on manufacturing equipment.

---

## 2. Block Kit Payload Example

```json
{
  "blocks": [
    {
      "type": "header",
      "text": { "type": "plain_text", "text": "🚨 Urgent Human Approval Required: AP Invoice $14,250" }
    },
    {
      "type": "section",
      "fields": [
        { "type": "mrkdwn", "text": "*Vendor:* Apex Precision" },
        { "type": "mrkdwn", "text": "*PO Ref:* PO-9014" },
        { "type": "mrkdwn", "text": "*Risk Tier:* HIGH" },
        { "type": "mrkdwn", "text": "*Match Status:* 100% 3-Way Match" }
      ]
    },
    {
      "type": "actions",
      "elements": [
        {
          "type": "button",
          "text": { "type": "plain_text", "text": "Review & Authorize in Portal" },
          "style": "primary",
          "url": "https://portal.omniagent.io/approvals/appr_771829"
        }
      ]
    }
  ]
}
```
