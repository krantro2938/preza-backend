-- init-db/01-create-tables.sql

CREATE TABLE IF NOT EXISTS PRESENTATION_TEMPLATE (
    id SERIAL PRIMARY KEY,
    title VARCHAR(256),
    slides JSONB NOT NULL
);

CREATE TABLE IF NOT EXISTS PRESENTATION (
    id SERIAL PRIMARY KEY,
    title VARCHAR(256),
    description TEXT,
    presentation JSONB NOT NULL,
    generating BOOLEAN NOT NULL DEFAULT FALSE,
    slides_count INT CHECK (slides_count >= 0),
    presentation_url VARCHAR(512),
    presentation_template_id INT REFERENCES PRESENTATION_TEMPLATE(id) ON DELETE SET NULL
);