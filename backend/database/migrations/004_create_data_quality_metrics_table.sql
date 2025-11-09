-- Migration: Create data_quality_metrics table
-- Purpose: Store data quality validation results (diversity, leakage, etc.)
-- For thesis documentation and analysis

CREATE TABLE IF NOT EXISTS data_quality_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_id INTEGER NOT NULL,
    
    -- Validation metadata
    validation_type VARCHAR(50) NOT NULL,  -- 'training', 'on_demand', 'scheduled'
    validation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Sample information
    total_samples INTEGER NOT NULL,
    train_samples INTEGER,
    test_samples INTEGER,
    
    -- Diversity metrics
    diversity_score REAL,  -- 0.0 to 1.0
    unique_sequences INTEGER,
    structure_diversity REAL,  -- For template-specific analysis
    content_diversity REAL,    -- For field value analysis
    
    -- Data leakage metrics
    leakage_detected BOOLEAN DEFAULT 0,
    leakage_similarity_max REAL,  -- Max similarity found
    leakage_samples_checked INTEGER,
    leakage_samples_flagged INTEGER,
    
    -- Label distribution (JSON)
    label_distribution TEXT,  -- JSON: {"B-NAMA": 100, "I-NAMA": 250, ...}
    
    -- Recommendations (JSON)
    recommendations TEXT,  -- JSON: ["✅ Good diversity", "⚠️ Low samples", ...]
    
    -- Performance impact
    validation_duration_seconds REAL,
    
    -- Status
    status VARCHAR(20) DEFAULT 'completed',  -- 'pending', 'running', 'completed', 'failed'
    error_message TEXT,
    
    -- Metadata
    triggered_by VARCHAR(50),  -- 'training', 'api', 'scheduled', 'manual'
    notes TEXT,
    
    FOREIGN KEY (template_id) REFERENCES templates(id) ON DELETE CASCADE
);

-- Indexes for efficient queries
CREATE INDEX IF NOT EXISTS idx_dqm_template_id ON data_quality_metrics(template_id);
CREATE INDEX IF NOT EXISTS idx_dqm_validation_date ON data_quality_metrics(validation_date);
CREATE INDEX IF NOT EXISTS idx_dqm_validation_type ON data_quality_metrics(validation_type);
CREATE INDEX IF NOT EXISTS idx_dqm_status ON data_quality_metrics(status);

-- View for latest metrics per template
CREATE VIEW IF NOT EXISTS latest_data_quality_metrics AS
SELECT 
    dqm.*,
    t.name as template_name
FROM data_quality_metrics dqm
INNER JOIN templates t ON dqm.template_id = t.id
WHERE dqm.id IN (
    SELECT MAX(id)
    FROM data_quality_metrics
    GROUP BY template_id
);
