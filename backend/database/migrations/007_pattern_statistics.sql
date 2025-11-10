-- Migration: Pattern Statistics (Prefix/Suffix/Noise Learning)
-- Date: 2025-11-09
-- Purpose: Store learned pattern statistics in database instead of JSON files

-- ============================================================================
-- Pattern Statistics Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS pattern_statistics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    field_config_id INTEGER NOT NULL,
    statistic_type TEXT NOT NULL,  -- 'prefix', 'suffix', 'structural_noise'
    pattern_value TEXT NOT NULL,   -- The actual prefix/suffix/noise pattern
    frequency INTEGER DEFAULT 1,   -- How many times seen
    confidence REAL DEFAULT 0.0,   -- Confidence score (0.0 - 1.0)
    sample_count INTEGER DEFAULT 0, -- Total samples analyzed
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata TEXT,  -- JSON: additional info
    
    FOREIGN KEY (field_config_id) REFERENCES field_configs(id) ON DELETE CASCADE,
    
    -- Ensure unique statistics per field
    UNIQUE(field_config_id, statistic_type, pattern_value)
);

-- ============================================================================
-- Indexes for Performance
-- ============================================================================
CREATE INDEX IF NOT EXISTS idx_pattern_statistics_field 
ON pattern_statistics(field_config_id, is_active);

CREATE INDEX IF NOT EXISTS idx_pattern_statistics_type 
ON pattern_statistics(statistic_type, is_active);

CREATE INDEX IF NOT EXISTS idx_pattern_statistics_frequency 
ON pattern_statistics(field_config_id, frequency DESC);

-- ============================================================================
-- Pattern Statistics Types
-- ============================================================================
-- statistic_type values:
--   'prefix'            - Common prefix to remove (e.g., "tanggal", "peserta")
--   'suffix'            - Common suffix to remove (e.g., "tahun", "bulan")
--   'structural_noise'  - Structural patterns (e.g., "has_parentheses_both")
--
-- For structural_noise, pattern_value is the noise type:
--   'has_parentheses_both'
--   'has_parentheses_start'
--   'has_parentheses_end'
--   'has_quotes'
--   'has_brackets'
--   'has_trailing_comma'
--   'has_trailing_period'
--   'has_multiple_names'  -- e.g., "Name1) (Name2"
--   'has_location_prefix' -- e.g., "Kota, Date"
--
-- ============================================================================

-- Verification queries:
-- SELECT COUNT(*) FROM pattern_statistics;
-- SELECT field_config_id, statistic_type, COUNT(*) FROM pattern_statistics GROUP BY field_config_id, statistic_type;
