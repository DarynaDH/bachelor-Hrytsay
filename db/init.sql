CREATE TABLE IF NOT EXISTS players (
    player_id      INTEGER PRIMARY KEY,
    player_name    VARCHAR(128),
    first_seen     TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_seen      TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    total_sessions INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS events (
    id          SERIAL PRIMARY KEY,
    server_id   VARCHAR(64)  NOT NULL,
    event_type  VARCHAR(64)  NOT NULL,
    player_id   INTEGER,
    player_name VARCHAR(128),
    payload     JSONB,
    created_at  TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT fk_events_player 
        FOREIGN KEY (player_id) 
        REFERENCES players(player_id) 
        ON DELETE SET NULL 
        DEFERRABLE INITIALLY DEFERRED
);

CREATE INDEX IF NOT EXISTS idx_events_created_at ON events (created_at);
CREATE INDEX IF NOT EXISTS idx_events_player_id  ON events (player_id);
CREATE INDEX IF NOT EXISTS idx_events_event_type ON events (event_type);