-- ================================
-- Schema for Notes/Links Service
-- ================================

PRAGMA foreign_keys = ON;

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_user_id BIGINT NOT NULL UNIQUE,
    first_seen_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_seen_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Items table
CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_user_id INTEGER NOT NULL,
    short_code TEXT NOT NULL UNIQUE,
    kind TEXT NOT NULL CHECK(kind IN ('url', 'note')),
    content TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL,
    FOREIGN KEY (owner_user_id) REFERENCES users (id) ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_users_telegram_user_id ON users (telegram_user_id);
CREATE INDEX IF NOT EXISTS idx_items_short_code ON items (short_code);
CREATE INDEX IF NOT EXISTS idx_items_owner_user_id ON items (owner_user_id);

-- Trigger to update last_seen_at when a user is updated
CREATE TRIGGER IF NOT EXISTS trg_users_update_last_seen
AFTER UPDATE ON users
BEGIN
    UPDATE users SET last_seen_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;
