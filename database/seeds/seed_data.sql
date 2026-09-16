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

-- 3. Business Machines & Production Records
INSERT INTO machines (id, organization_id, name, machine_code, status, failure_count)
VALUES
  ('30000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000001', 'Robotic Welder Alpha', 'RWA-01', 'OPERATIONAL', 3),
  ('30000000-0000-0000-0000-000000000002', '00000000-0000-0000-0000-000000000001', 'CNC Milling Station Beta', 'CMS-02', 'MAINTENANCE', 7),
  ('30000000-0000-0000-0000-000000000003', '00000000-0000-0000-0000-000000000001', 'High-Speed Stamper Gamma', 'HSS-03', 'FAILED', 14)
ON CONFLICT DO NOTHING;

INSERT INTO production_records (id, organization_id, machine_id, batch_number, status, defect_count, production_time_hours)
VALUES
  ('31000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000001', '30000000-0000-0000-0000-000000000001', 'BATCH-2026-09A', 'PASSED', 0, 4.5),
  ('31000000-0000-0000-0000-000000000002', '00000000-0000-0000-0000-000000000001', '30000000-0000-0000-0000-000000000002', 'BATCH-2026-09B', 'FAILED', 12, 6.2),
  ('31000000-0000-0000-0000-000000000003', '00000000-0000-0000-0000-000000000001', '30000000-0000-0000-0000-000000000003', 'BATCH-2026-09C', 'FAILED', 18, 5.8)
ON CONFLICT DO NOTHING;

-- 4. Orders, Products & Vendors
INSERT INTO orders (id, organization_id, order_number, customer_name, status, total_amount)
VALUES
  ('40000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000001', 'ORD-2026-001', 'Acme Aerospace', 'PENDING', 24500.00),
  ('40000000-0000-0000-0000-000000000002', '00000000-0000-0000-0000-000000000001', 'ORD-2026-002', 'Apex Logistics', 'PENDING', 8900.50),
  ('40000000-0000-0000-0000-000000000003', '00000000-0000-0000-0000-000000000001', 'ORD-2026-003', 'BioCore Systems', 'COMPLETED', 14320.00)
ON CONFLICT DO NOTHING;

INSERT INTO products (id, organization_id, name, sku, category, price, usage_count, is_active)
VALUES
  ('50000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000001', 'Precision Servo Actuator', 'ACT-100', 'Actuators', 1250.00, 340, TRUE),
  ('50000000-0000-0000-0000-000000000002', '00000000-0000-0000-0000-000000000001', 'Industrial LiDAR Sensor', 'LDR-500', 'Sensors', 3400.00, 185, TRUE),
  ('50000000-0000-0000-0000-000000000003', '00000000-0000-0000-0000-000000000001', 'Hydraulic Pressure Valve', 'VLV-020', 'Hydraulics', 450.00, 520, TRUE)
ON CONFLICT DO NOTHING;

INSERT INTO vendors (id, organization_id, name, contact_email, total_purchases, rating)
VALUES
  ('60000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000001', 'CyberAlloy Steelworks', 'sales@cyberalloy.com', 85400.00, 4.8),
  ('60000000-0000-0000-0000-000000000002', '00000000-0000-0000-0000-000000000001', 'NexGen Polymers Corp', 'orders@nexgenpolymers.com', 41200.00, 4.5)
ON CONFLICT DO NOTHING;

