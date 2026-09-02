-- =============================================================================
-- OmniAgent AI — Baseline Enterprise Seed Data
-- =============================================================================

-- 1. Default Organization & Department
INSERT INTO organizations (id, name, slug)
VALUES ('00000000-0000-0000-0000-000000000001', 'OmniCorp Enterprise', 'omnicorp')
ON CONFLICT (slug) DO NOTHING;

INSERT INTO departments (id, organization_id, name, code)
VALUES 
  ('10000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000001', 'Information Technology', 'IT'),
  ('10000000-0000-0000-0000-000000000002', '00000000-0000-0000-0000-000000000001', 'Finance & Accounting', 'FIN'),
  ('10000000-0000-0000-0000-000000000003', '00000000-0000-0000-0000-000000000001', 'Human Resources', 'HR')
ON CONFLICT (organization_id, code) DO NOTHING;

-- 2. System Roles
INSERT INTO roles (id, name, description, is_system_role)
VALUES 
  ('20000000-0000-0000-0000-000000000001', 'Owner', 'Full control over the organization and billing', TRUE),
  ('20000000-0000-0000-0000-000000000002', 'Admin', 'System configuration and user management', TRUE),
  ('20000000-0000-0000-0000-000000000003', 'Supervisor', 'Approves high-risk agent workflows and manages tasks', TRUE),
  ('20000000-0000-0000-0000-000000000004', 'Operator', 'Runs agent tasks and interacts with workflows', TRUE),
  ('20000000-0000-0000-0000-000000000005', 'Auditor', 'Read-only access to audit logs and trace history', TRUE),
  ('20000000-0000-0000-0000-000000000006', 'Viewer', 'Read-only access to authorized public dashboards', TRUE)
ON CONFLICT DO NOTHING;
