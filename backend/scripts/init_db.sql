-- MindEase DB Initialization Script
-- Enables pgvector extension for vector similarity search

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE mindease_db TO mindease_user;
