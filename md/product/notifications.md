# Product — Notification Hub & Alert Delivery Channels

## Status
**Status:** ✅ IMPLEMENTED (In-App Toast, WebSockets, Email & Slack)

---

## 1. Multi-Channel Notification Routing

OmniAgent AI routes operational notifications based on urgency and user role subscriptions:

| Event Type | Urgency | Delivery Channels | Recipient Roles |
| :--- | :--- | :--- | :--- |
| **High-Risk Human Approval Required** | Immediate | In-App Modal + Slack + Email | Manager, Admin |
| **Workflow Run Completed** | Low | In-App Toast + Activity Feed | Triggering User |
| **Document Ingestion Failed** | Medium | In-App Toast + Email | Uploader, Admin |
| **Monthly Token Budget Threshold (80%)**| High | In-App Banner + Email | Admin |
