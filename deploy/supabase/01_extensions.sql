-- ==============================================================================
-- OmniAgent AI — Supabase Database Initialization: Extensions
-- ==============================================================================

-- 1. Enable pgvector for semantic vector embeddings retrieval
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Enable UUID generation functions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 3. Enable trigram matching for full-text and hybrid retrieval
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- 4. Enable pgcrypto for cryptographic utilities
CREATE EXTENSION IF NOT EXISTS pgcrypto;
