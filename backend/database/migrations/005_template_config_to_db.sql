-- Migration: Move template configs from JSON files to database
-- Date: 2025-11-09
-- Purpose: Enable versioning, concurrent access, and adaptive pattern management

-- ============================================================================
-- 1. Template Configurations (Header)
-- ============================================================================
CREATE TABLE IF NOT EXISTS template_configs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_id INTEGER NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT,
    is_active BOOLEAN DEFAULT 1,
    FOREIGN KEY (template_id) REFERENCES templates(id) ON DELETE CASCADE,
    UNIQUE(template_id, version)
);

CREATE INDEX IF NOT EXISTS idx_template_configs_active 
ON template_configs(template_id, is_active) 
WHERE is_active = 1;

-- ============================================================================
-- 2. Field Configurations
-- ============================================================================
CREATE TABLE IF NOT EXISTS field_configs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    config_id INTEGER NOT NULL,
    field_name TEXT NOT NULL,
    field_type TEXT,
    base_pattern TEXT,
    confidence_threshold REAL DEFAULT 0.7,
    extraction_order INTEGER DEFAULT 0,
    is_required BOOLEAN DEFAULT 0,
    validation_rules TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (config_id) REFERENCES template_configs(id) ON DELETE CASCADE,
    UNIQUE(config_id, field_name)
);

CREATE INDEX IF NOT EXISTS idx_field_configs_lookup 
ON field_configs(config_id, field_name);

-- ============================================================================
-- 3. Field Locations (Multi-location support)
-- ============================================================================
CREATE TABLE IF NOT EXISTS field_locations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    field_config_id INTEGER NOT NULL,
    page INTEGER DEFAULT 0,
    x0 REAL NOT NULL,
    y0 REAL NOT NULL,
    x1 REAL NOT NULL,
    y1 REAL NOT NULL,
    label TEXT,
    location_index INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (field_config_id) REFERENCES field_configs(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_field_locations_lookup 
ON field_locations(field_config_id, page);

-- ============================================================================
-- 4. Learned Patterns (Adaptive Learning!)
-- ============================================================================
CREATE TABLE IF NOT EXISTS learned_patterns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    field_config_id INTEGER NOT NULL,
    pattern TEXT NOT NULL,
    pattern_type TEXT NOT NULL,
    description TEXT,
    frequency INTEGER DEFAULT 0,
    match_rate REAL,
    confidence_boost REAL DEFAULT 0.0,
    priority INTEGER DEFAULT 0,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMP,
    usage_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT 1,
    examples TEXT,
    metadata TEXT,
    FOREIGN KEY (field_config_id) REFERENCES field_configs(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_learned_patterns_active 
ON learned_patterns(field_config_id, is_active, priority DESC) 
WHERE is_active = 1;

CREATE INDEX IF NOT EXISTS idx_learned_patterns_performance 
ON learned_patterns(field_config_id, match_rate DESC, usage_count DESC);

-- 1. Create indexes for performance (usage tracking queries)
CREATE INDEX IF NOT EXISTS idx_learned_patterns_usage 
ON learned_patterns(usage_count, match_rate, is_active);

-- 2. Create index for pattern lookup
CREATE INDEX IF NOT EXISTS idx_learned_patterns_field_active 
ON learned_patterns(field_config_id, is_active, priority DESC);

-- ============================================================================
-- 5. Config Change History (Audit Trail)
-- ============================================================================
CREATE TABLE IF NOT EXISTS config_change_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    config_id INTEGER NOT NULL,
    change_type TEXT NOT NULL,
    changed_by TEXT,
    changes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (config_id) REFERENCES template_configs(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_config_history_lookup 
ON config_change_history(config_id, created_at DESC);

-- ============================================================================
-- 6. Pattern Learning Jobs (Track optimization runs)
-- ============================================================================
CREATE TABLE IF NOT EXISTS pattern_learning_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_id INTEGER NOT NULL,
    field_name TEXT,
    job_type TEXT NOT NULL,
    status TEXT NOT NULL,
    feedback_count INTEGER DEFAULT 0,
    patterns_discovered INTEGER DEFAULT 0,
    patterns_applied INTEGER DEFAULT 0,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,
    result_summary TEXT,
    FOREIGN KEY (template_id) REFERENCES templates(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_pattern_jobs_status 
ON pattern_learning_jobs(template_id, status, started_at DESC);

-- ============================================================================
-- 7. Views for Easy Querying
-- ============================================================================
CREATE VIEW IF NOT EXISTS v_active_template_configs AS
SELECT 
    tc.id as config_id,
    tc.template_id,
    tc.version,
    t.name as template_name,
    COUNT(DISTINCT fc.id) as field_count,
    COUNT(DISTINCT lp.id) as learned_pattern_count,
    tc.created_at,
    tc.created_by
FROM template_configs tc
JOIN templates t ON tc.template_id = t.id
LEFT JOIN field_configs fc ON tc.id = fc.config_id
LEFT JOIN learned_patterns lp ON fc.id = lp.field_config_id AND lp.is_active = 1
WHERE tc.is_active = 1
GROUP BY tc.id;

CREATE VIEW IF NOT EXISTS v_pattern_performance AS
SELECT 
    lp.id as pattern_id,
    fc.field_name,
    t.name as template_name,
    lp.pattern,
    lp.pattern_type,
    lp.usage_count,
    lp.success_count,
    CASE 
        WHEN lp.usage_count > 0 
        THEN ROUND(CAST(lp.success_count AS REAL) / lp.usage_count * 100, 2)
        ELSE 0 
    END as success_rate,
    lp.match_rate,
    lp.priority,
    lp.last_used_at
FROM learned_patterns lp
JOIN field_configs fc ON lp.field_config_id = fc.id
JOIN template_configs tc ON fc.config_id = tc.id
JOIN templates t ON tc.template_id = t.id
WHERE lp.is_active = 1
ORDER BY lp.usage_count DESC;
