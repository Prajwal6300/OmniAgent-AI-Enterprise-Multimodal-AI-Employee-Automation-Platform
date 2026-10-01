-- =============================================================================
-- OmniAgent AI — Baseline Enterprise Seed Data (Roles, Permissions & Runnable Workflows)
-- =============================================================================

-- 1. Default Organization & Department Bootstrap
INSERT INTO organizations (id, name, slug)
VALUES ('00000000-0000-0000-0000-000000000001', 'OmniCorp Enterprise', 'omnicorp')
ON CONFLICT (slug) DO NOTHING;

INSERT INTO departments (id, organization_id, name, code)
VALUES 
  ('10000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000001', 'Engineering & Operations', 'ENG'),
  ('10000000-0000-0000-0000-000000000002', '00000000-0000-0000-0000-000000000001', 'Finance & Compliance', 'FIN')
ON CONFLICT (organization_id, code) DO NOTHING;

-- 2. 6-Role System Hierarchy
INSERT INTO roles (id, name, description, is_system_role)
VALUES 
  ('20000000-0000-0000-0000-000000000001', 'Owner', 'Full organization control, billing, and owner delegation', TRUE),
  ('20000000-0000-0000-0000-000000000002', 'Admin', 'User management, integrations, and policy configuration', TRUE),
  ('20000000-0000-0000-0000-000000000003', 'Supervisor', 'Human-in-the-loop authorization and workflow supervision', TRUE),
  ('20000000-0000-0000-0000-000000000004', 'Operator', 'Runs agent workflows, document processing, and chat tasks', TRUE),
  ('20000000-0000-0000-0000-000000000005', 'Auditor', 'Cryptographic audit log verification and trace inspections', TRUE),
  ('20000000-0000-0000-0000-000000000006', 'Viewer', 'Read-only access to published analytics and reports', TRUE)
ON CONFLICT DO NOTHING;

-- 3. Granular System Permissions
INSERT INTO permissions (id, name, description, category)
VALUES
  ('21000000-0000-0000-0000-000000000001', 'org:manage', 'Manage organization settings and members', 'admin'),
  ('21000000-0000-0000-0000-000000000002', 'users:read', 'View organization users and roles', 'users'),
  ('21000000-0000-0000-0000-000000000003', 'users:write', 'Invite users and change role assignments', 'users'),
  ('21000000-0000-0000-0000-000000000004', 'documents:read', 'Read and query documents in knowledge base', 'documents'),
  ('21000000-0000-0000-0000-000000000005', 'documents:write', 'Upload, parse, and index document chunks', 'documents'),
  ('21000000-0000-0000-0000-000000000006', 'chat:execute', 'Execute conversational multi-agent inquiries', 'agents'),
  ('21000000-0000-0000-0000-000000000007', 'actions:execute', 'Dispatch authorized operational actions', 'actions'),
  ('21000000-0000-0000-0000-000000000008', 'approvals:decide', 'Approve or reject pending human-in-the-loop requests', 'approvals'),
  ('21000000-0000-0000-0000-000000000009', 'workflows:manage', 'Create, edit, and trigger automated workflows', 'workflows'),
  ('21000000-0000-0000-0000-000000000010', 'audit:verify', 'Read and verify cryptographic audit hash chains', 'audit'),
  ('21000000-0000-0000-0000-000000000011', 'integrations:manage', 'Configure external third-party integrations', 'integrations')
ON CONFLICT DO NOTHING;

-- 4. Role-Permission Mappings
-- Owner: All permissions
INSERT INTO role_permissions (role_id, permission_id)
SELECT '20000000-0000-0000-0000-000000000001', id FROM permissions
ON CONFLICT DO NOTHING;

-- Admin: All permissions except owner-exclusive org deletion
INSERT INTO role_permissions (role_id, permission_id)
SELECT '20000000-0000-0000-0000-000000000002', id FROM permissions
WHERE name != 'org:manage'
ON CONFLICT DO NOTHING;

-- Supervisor: Approvals, actions, workflows, documents, chat
INSERT INTO role_permissions (role_id, permission_id)
SELECT '20000000-0000-0000-0000-000000000003', id FROM permissions
WHERE name IN ('approvals:decide', 'actions:execute', 'workflows:manage', 'documents:read', 'documents:write', 'chat:execute', 'users:read')
ON CONFLICT DO NOTHING;

-- Operator: Documents, chat, workflow trigger
INSERT INTO role_permissions (role_id, permission_id)
SELECT '20000000-0000-0000-0000-000000000004', id FROM permissions
WHERE name IN ('documents:read', 'documents:write', 'chat:execute', 'workflows:manage')
ON CONFLICT DO NOTHING;

-- Auditor: Audit verify, documents read, users read
INSERT INTO role_permissions (role_id, permission_id)
SELECT '20000000-0000-0000-0000-000000000005', id FROM permissions
WHERE name IN ('audit:verify', 'documents:read', 'users:read')
ON CONFLICT DO NOTHING;

-- Viewer: Documents read
INSERT INTO role_permissions (role_id, permission_id)
SELECT '20000000-0000-0000-0000-000000000006', id FROM permissions
WHERE name IN ('documents:read')
ON CONFLICT DO NOTHING;

-- 5. Real, Runnable Seed Workflows (Built strictly from working steps)
INSERT INTO workflows (id, organization_id, name, description, trigger_type, definition, is_active)
VALUES
  (
    '70000000-0000-0000-0000-000000000001',
    '00000000-0000-0000-0000-000000000001',
    'Automated Document Ingestion & RAG Indexing',
    'Processes uploaded enterprise documents, chunks text, creates vector embeddings, and alerts team.',
    'MANUAL',
    '{
      "steps": [
        {
          "id": "step_extract",
          "name": "Extract Document Pages",
          "action": "document_extract",
          "params": {"allowed_types": ["pdf", "docx", "txt"]}
        },
        {
          "id": "step_index",
          "name": "Generate Vector Embeddings",
          "action": "rag_index",
          "params": {"chunk_size": 500, "chunk_overlap": 50},
          "depends_on": ["step_extract"]
        },
        {
          "id": "step_notify",
          "name": "Notify Ingestion Completed",
          "action": "send_notification",
          "params": {"channel": "IN_APP", "title": "Document Indexing Completed"},
          "depends_on": ["step_index"]
        }
      ]
    }',
    TRUE
  ),
  (
    '70000000-0000-0000-0000-000000000002',
    '00000000-0000-0000-0000-000000000001',
    'Security Audit Verification & Alerting',
    'Verifies SHA-256 cryptographic audit hash chains and issues alert on any anomaly detection.',
    'SCHEDULE',
    '{
      "schedule": "0 */4 * * *",
      "steps": [
        {
          "id": "step_audit_verify",
          "name": "Verify Audit Log Hashes",
          "action": "audit_verify",
          "params": {"max_entries": 1000}
        },
        {
          "id": "step_eval_risk",
          "name": "Evaluate Chain Integrity",
          "action": "risk_evaluate",
          "params": {"threshold": 1.0},
          "depends_on": ["step_audit_verify"]
        },
        {
          "id": "step_alert",
          "name": "Dispatch Audit Status Notification",
          "action": "send_notification",
          "params": {"channel": "IN_APP", "title": "Audit Chain Verification Succeeded"},
          "depends_on": ["step_eval_risk"]
        }
      ]
    }',
    TRUE
  )
ON CONFLICT DO NOTHING;
