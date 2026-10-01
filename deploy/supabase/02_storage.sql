-- ==============================================================================
-- OmniAgent AI — Supabase Storage Bucket Initialization
-- ==============================================================================

-- Create buckets for tenant documents and multimodal media assets
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES 
    (
        'omniagent-documents',
        'omniagent-documents',
        false,
        52428800, -- 50MB
        ARRAY['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain', 'text/csv']
    ),
    (
        'omniagent-media',
        'omniagent-media',
        false,
        20971520, -- 20MB
        ARRAY['image/png', 'image/jpeg', 'image/webp']
    )
ON CONFLICT (id) DO UPDATE SET
    public = EXCLUDED.public,
    file_size_limit = EXCLUDED.file_size_limit,
    allowed_mime_types = EXCLUDED.allowed_mime_types;

-- Storage object policies enforcing path-based organization prefix:
-- Format: <organization_id>/<file_path>
CREATE POLICY "Tenant Storage Access Policy"
ON storage.objects
FOR ALL
USING (
    bucket_id IN ('omniagent-documents', 'omniagent-media')
    -- Ensures users can only access objects within their own tenant folder
    AND (storage.foldername(name))[1] = auth.jwt() ->> 'organization_id'
)
WITH CHECK (
    bucket_id IN ('omniagent-documents', 'omniagent-media')
    AND (storage.foldername(name))[1] = auth.jwt() ->> 'organization_id'
);
