CREATE TABLE PRESENTATION_TEMPLATE (
    id SERIAL PRIMARY KEY,
    title VARCHAR(256),
    slides JSONB
);

CREATE TABLE PRESENTATION (
    id SERIAL PRIMARY KEY,
    title VARCHAR(256),
    description TEXT,
    presentation JSONB,
    generating BOOLEAN,
    slides_count INT,
    presentation_url VARCHAR(512),

    presentation_template_id INT REFERENCES PRESENTATION_TEMPLATE(id)
);
