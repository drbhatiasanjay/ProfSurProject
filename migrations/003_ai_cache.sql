CREATE TABLE IF NOT EXISTS ai_cache (
    query_hash   TEXT NOT NULL,
    context_hash TEXT NOT NULL,
    model        TEXT NOT NULL,
    response     TEXT NOT NULL,
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (query_hash, context_hash, model)
);
