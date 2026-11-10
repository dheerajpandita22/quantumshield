-- QuantumShield Database Initialization
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS security_events (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_type  VARCHAR(64) NOT NULL,
    severity    VARCHAR(16) NOT NULL,
    source      VARCHAR(64),
    description TEXT,
    resolved    BOOLEAN DEFAULT FALSE,
    metadata    JSONB,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS quantum_jobs (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    circuit_type VARCHAR(64) NOT NULL,
    backend_id  VARCHAR(64) NOT NULL,
    shots       INTEGER NOT NULL DEFAULT 1024,
    status      VARCHAR(16) NOT NULL DEFAULT 'QUEUED',
    parameters  JSONB,
    result      JSONB,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);
