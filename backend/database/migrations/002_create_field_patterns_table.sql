-- Migration: Create field_patterns table for adaptive pattern learning
-- This table stores regex patterns learned from user usage

CREATE TABLE IF NOT EXISTS field_patterns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    field_name TEXT NOT NULL,
    regex_pattern TEXT NOT NULL,
    user_id INTEGER,  -- NULL for global patterns, specific ID for user patterns
    usage_count INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Ensure unique combination of field_name, pattern, and user
    UNIQUE(field_name, regex_pattern, user_id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_field_patterns_field_name 
    ON field_patterns(field_name);

CREATE INDEX IF NOT EXISTS idx_field_patterns_user_id 
    ON field_patterns(user_id);

CREATE INDEX IF NOT EXISTS idx_field_patterns_usage 
    ON field_patterns(usage_count DESC);

CREATE INDEX IF NOT EXISTS idx_field_patterns_updated 
    ON field_patterns(updated_at DESC);

-- Insert some common default patterns
INSERT OR IGNORE INTO field_patterns (field_name, regex_pattern, user_id, usage_count) VALUES
    ('tanggal', '\d{1,2}[-/]\d{1,2}[-/]\d{2,4}', NULL, 10),
    ('tanggal', '\d{1,2}[-/][\w\s]+[-/]\d{2,4}', NULL, 5),  -- Format: 15/Januari/2024
    ('email', '[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', NULL, 10),
    ('nama', '[A-Za-z\s\.]+', NULL, 10),
    ('telepon', '[\d\-\+\(\)\s]{10,}', NULL, 10),
    ('alamat', '[A-Za-z0-9\s\.,\-]+', NULL, 10),
    ('nik', '\d{16}', NULL, 10),
    ('tempat_lahir', '[A-Za-z\s]+', NULL, 10);
