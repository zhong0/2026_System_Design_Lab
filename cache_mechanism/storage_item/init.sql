CREATE TABLE short_links (
    id           BIGSERIAL PRIMARY KEY,
    code         VARCHAR(10)  NOT NULL UNIQUE,
    original_url TEXT         NOT NULL,
    created_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    expires_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW() + INTERVAL '1 day'
);

CREATE INDEX idx_short_links_code ON short_links (code);