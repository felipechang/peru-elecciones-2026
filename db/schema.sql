-- Peru Elecciones 2026 — Database Schema
-- Milestone 1: Database schema design and setup
CREATE TABLE IF NOT EXISTS parties
(
    id         SERIAL PRIMARY KEY,
    name       TEXT        NOT NULL UNIQUE,
    summary    TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS candidates
(
    id         SERIAL PRIMARY KEY,
    party_id   INTEGER     NOT NULL REFERENCES parties (id) ON DELETE CASCADE,
    name       TEXT        NOT NULL,
    position   TEXT        NOT NULL,
    -- e.g. Presidente, Vicepresidente, Senador, Congresista, Parlamento Andino
    scope      TEXT,
    -- e.g. nacional, departamento name
    list_order INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_candidates_party_id ON candidates (party_id);
CREATE INDEX IF NOT EXISTS idx_candidates_position ON candidates (position);
CREATE TABLE IF NOT EXISTS topics
(
    id         SERIAL PRIMARY KEY,
    name       TEXT        NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS party_sections
(
    id         SERIAL PRIMARY KEY,
    party_id   INTEGER     NOT NULL REFERENCES parties (id) ON DELETE CASCADE,
    topic_id   INTEGER     NOT NULL REFERENCES topics (id) ON DELETE CASCADE,
    content    TEXT        NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (party_id, topic_id)
);
CREATE INDEX IF NOT EXISTS idx_party_sections_party_id ON party_sections (party_id);
CREATE INDEX IF NOT EXISTS idx_party_sections_topic_id ON party_sections (topic_id);
CREATE TABLE IF NOT EXISTS events
(
    id           SERIAL PRIMARY KEY,
    candidate_id INTEGER     NOT NULL REFERENCES candidates (id) ON DELETE CASCADE,
    title        TEXT        NOT NULL,
    summary      TEXT,
    event_date   DATE,
    source       TEXT,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_events_candidate_id ON events (candidate_id);
CREATE INDEX IF NOT EXISTS idx_events_event_date ON events (event_date DESC);
