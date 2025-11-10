-- ============================================================================
-- Migration 006: Add field_contexts table
-- Date: 2025-11-11
-- Purpose: Store context information (label_position, words_before, words_after)
--          Structure matches JSON format from template analysis
-- ============================================================================

-- Create field_contexts table
CREATE TABLE IF NOT EXISTS field_contexts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    field_location_id INTEGER NOT NULL,
    
    -- Label information
    label TEXT,
    
    -- Label position (bounding box)
    label_position TEXT, -- JSON: {"x0": ..., "y0": ..., "x1": ..., "y1": ...}
    
    -- Context words
    words_before TEXT,   -- JSON array: [{"text": "...", "x": ..., "y": ...}, ...]
    words_after TEXT,    -- JSON array: [{"text": "...", "x": ..., "y": ...}, ...]
    next_field_y REAL,  -- Y position of next field
    typical_length INTEGER,  -- Typical field length in chars
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (field_location_id) REFERENCES field_locations(id) ON DELETE CASCADE
);

-- ============================================================================
-- Notes:
-- ============================================================================
-- next_field_y: Y-coordinate of next field (helps model know when to stop)
-- typical_length: Expected length of field value (learned from feedback)
--
-- Example for event_location:
--   next_field_y: 380 (issue_place position)
--   typical_length: 45 (average address length)
--
-- This is MINIMAL optimization - only what we need for current problem
-- ============================================================================


-- Create indexes for faster queries
CREATE INDEX IF NOT EXISTS idx_field_contexts_location 
ON field_contexts(field_location_id);

-- ============================================================================
-- Notes:
-- ============================================================================
-- This table stores context information that helps CRF model learn:
-- 1. Where labels are positioned relative to field values
-- 2. What words appear before/after field values
-- 3. Spatial relationships between text elements
--
-- JSON Structure matches template config format:
-- {
--   "label": "Sertifikat:",
--   "label_position": {"x0": 217.6, "y0": 150.9, "x1": 281.9, "y1": 164.8},
--   "words_before": [{"text": "No.", "x": 204.1, "y": 157.9}, ...],
--   "words_after": [...]
-- }
--
-- This is CRITICAL for improving accuracy from 71% to 90%+
-- ============================================================================
