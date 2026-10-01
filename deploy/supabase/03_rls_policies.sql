-- ==============================================================================
-- OmniAgent AI — Supabase Row-Level Security (RLS) Tenant Isolation
-- ==============================================================================

-- Helper function to extract organization_id from current session or JWT claim
CREATE OR REPLACE FUNCTION current_org_id()
RETURNS UUID AS $$
BEGIN
    RETURN NULLIF(
        COALESCE(
            current_setting('request.jwt.claims', true)::jsonb ->> 'organization_id',
            current_setting('app.current_organization_id', true)
        ),
        ''
    )::UUID;
EXCEPTION
    WHEN OTHERS THEN
        RETURN NULL;
END;
$$ LANGUAGE plpgsql STABLE SECURITY DEFINER;

-- 1. Enable RLS on core tenant tables
ALTER TABLE organizations ENABLE ROW LEVEL SECURITY;
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE document_chunks ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE workflows ENABLE ROW LEVEL SECURITY;
ALTER TABLE workflow_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE integrations ENABLE ROW LEVEL SECURITY;
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE approvals ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;

-- 2. Organizations policy
CREATE POLICY org_isolation_policy ON organizations
    FOR ALL
    USING (id = current_org_id())
    WITH CHECK (id = current_org_id());

-- 3. Users policy
CREATE POLICY users_isolation_policy ON users
    FOR ALL
    USING (organization_id = current_org_id())
    WITH CHECK (organization_id = current_org_id());

-- 4. Documents policy
CREATE POLICY documents_isolation_policy ON documents
    FOR ALL
    USING (organization_id = current_org_id())
    WITH CHECK (organization_id = current_org_id());

-- 5. Document chunks policy
CREATE POLICY document_chunks_isolation_policy ON document_chunks
    FOR ALL
    USING (organization_id = current_org_id())
    WITH CHECK (organization_id = current_org_id());

-- 6. Conversations policy
CREATE POLICY conversations_isolation_policy ON conversations
    FOR ALL
    USING (organization_id = current_org_id())
    WITH CHECK (organization_id = current_org_id());

-- 7. Messages policy
CREATE POLICY messages_isolation_policy ON messages
    FOR ALL
    USING (organization_id = current_org_id())
    WITH CHECK (organization_id = current_org_id());

-- 8. Workflows policy
CREATE POLICY workflows_isolation_policy ON workflows
    FOR ALL
    USING (organization_id = current_org_id())
    WITH CHECK (organization_id = current_org_id());

-- 9. Workflow runs policy
CREATE POLICY workflow_runs_isolation_policy ON workflow_runs
    FOR ALL
    USING (organization_id = current_org_id())
    WITH CHECK (organization_id = current_org_id());

-- 10. Integrations policy
CREATE POLICY integrations_isolation_policy ON integrations
    FOR ALL
    USING (organization_id = current_org_id())
    WITH CHECK (organization_id = current_org_id());

-- 11. Notifications policy
CREATE POLICY notifications_isolation_policy ON notifications
    FOR ALL
    USING (organization_id = current_org_id())
    WITH CHECK (organization_id = current_org_id());

-- 12. Approvals policy
CREATE POLICY approvals_isolation_policy ON approvals
    FOR ALL
    USING (organization_id = current_org_id())
    WITH CHECK (organization_id = current_org_id());

-- 13. Audit logs policy (append and read only, never update/delete)
CREATE POLICY audit_logs_select_policy ON audit_logs
    FOR SELECT
    USING (organization_id = current_org_id());

CREATE POLICY audit_logs_insert_policy ON audit_logs
    FOR INSERT
    WITH CHECK (organization_id = current_org_id());
