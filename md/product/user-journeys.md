# Product — User Journeys & End-to-End Enterprise Experience

## Status
**Status:** ✅ IMPLEMENTED

---

## 1. Journey 1: Ad-Hoc Multimodal Chat Analysis
1. User logs into Next.js portal and navigates to `/chat`.
2. Drags and drops an invoice PDF and an equipment maintenance screenshot into the chatbox.
3. Types: *"Check if this invoice total matches our PO-9014 terms and inspect the photo for defects."*
4. AI Supervisor displays real-time agent execution stream in the thought accordion.
5. In the sidecar viewer, the user clicks citation `[1]` to see the highlighted invoice total on page 1, and inspects the bounding box overlay on the defect photo.
6. The AI notes a $14,250 total requires manager approval and provides a one-click button to queue the request.

---

## 2. Journey 2: Human Approval & Audit Verification
1. Finance Manager receives an urgent Slack alert with a deep-link to `/approvals/appr_771829`.
2. In the Next.js approval center, the manager reviews the 3-Way Match diff card showing 0.00% variance.
3. Manager clicks **"Authorize Payment"**.
4. Action Agent executes the SAP ERP mutation and displays confirmation document #SAP-DOC-099412.
5. Compliance Auditor opens `/audit` and verifies the green HMAC signature badge on the resulting transaction.
