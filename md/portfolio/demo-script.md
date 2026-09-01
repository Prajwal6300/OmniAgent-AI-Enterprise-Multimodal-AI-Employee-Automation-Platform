# Portfolio — 5-Minute Live Demonstration Script

---

## 🎬 5-Minute High-Impact Live Demo Script

### Scene 1: Introduction & Login (0:00 – 0:45)
* **Action:** Open `http://localhost:3000/login`. Log in as `finance.lead@acme.com`.
* **Talking Point:** *"Welcome to OmniAgent AI. Today, we're demonstrating an autonomous AI employee processing a multimodal vendor invoice reconciliation, grounding decisions in enterprise policies and relational databases, and gating financial mutations through a human approval workflow."*

---

### Scene 2: Multimodal Ingestion & Ad-Hoc Task (0:45 – 1:45)
* **Action:** Navigate to `/chat`. Drag and drop `invoice_8812.pdf` (Vendor: Apex Precision, Total: $14,250.00).
* **Prompt:** *"Verify this invoice against Purchase Order PO-9014 in our ERP, check if our travel & procurement policy covers these items, and if verified, prepare it for manager payment approval."*
* **Talking Point:** *"Watch the real-time agent execution stream in the thought accordion. The Supervisor instantly decomposes the request into 4 discrete sub-tasks: Document extraction, Database query, Policy RAG check, and Reasoning 3-way match."*

---

### Scene 3: Multimodal Extraction & Grounded Reasoning (1:45 – 2:45)
* **Action:** In the sidecar viewer, show the highlighted PDF bounding boxes for the 12 line items extracted by the Document Agent. Show the RAG citation chip referencing *Global Procurement Policy Section 3.2*.
* **Talking Point:** *"The Document Agent extracted 100% accurate line items. The Database Agent queried the PostgreSQL PO table, and the Reasoning Agent confirmed an exact 3-Way Match with 0.00% variance. Because the amount ($14,250) exceeds our $10,000 policy threshold, the workflow is automatically suspended as HIGH RISK."*

---

### Scene 4: Human-in-the-Loop Authorization (2:45 – 3:45)
* **Action:** Switch to `/approvals`. Show the pending approval card for Invoice #INV-2026-8812 with full AI thought reasoning and side-by-side reconciliation diff.
* **Action:** Click **"Authorize Payment & Post to SAP"**.
* **Talking Point:** *"The human manager reviews the verifiable evidence and authorizes the payment. Notice how the workflow resumes immediately—the Action Agent dispatches the authenticated REST API call to SAP ERP and returns SAP Document #099412."*

---

### Scene 5: Cryptographic Audit Trail & Telemetry (3:45 – 5:00)
* **Action:** Navigate to `/audit`. Filter by `resource_id = wf_run_991823`. Click the green **"Verified HMAC Signature"** badge.
* **Action:** Open the Agent Latency Waterfall tab showing total execution time of 5.8s and token breakdown.
* **Talking Point:** *"Every single step—from the initial PDF upload and SQL query to the manager's authorization and the ERP receipt—is permanently recorded in our tamper-proof HMAC audit ledger. This provides enterprise compliance officers with mathematical certainty of zero unauthorized AI mutations."*

---

## 🏭 Optional Manufacturing Defect Inspection Demo Flow

```text
1. Technician uploads machinery photo (turbine_blade.png) via mobile portal.
2. Vision Agent applies OpenCV contrast enhancement and flags a 0.8mm pitting micro-crack with bounding box [x:180, y:420].
3. RAG Agent queries Turbine Maintenance Manual QM-800, identifying that cracks > 0.2mm require ultrasonic evaluation.
4. Database Agent checks machine runtime (14,200 operating hours on Turbine #4).
5. Reasoning Agent classifies anomaly as CRITICAL and suspends workflow for Emergency Plant Supervisor Approval.
6. Plant Supervisor approves via SMS/Slack -> Action Agent generates SAP PM Work Order #99104.
```
