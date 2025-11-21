-- Migration 002: Template and Document Tables
-- Created: 2024-11-05
-- Description: Add templates, documents, and feedback tables

CREATE TABLE IF NOT EXISTS templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    filename TEXT NOT NULL,
    config_path TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    field_count INTEGER DEFAULT 0,
    status TEXT DEFAULT 'active'
);


CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_id INTEGER NOT NULL,
    filename TEXT NOT NULL,
    file_path TEXT NOT NULL,
    extraction_result TEXT,
    extraction_time_ms INTEGER DEFAULT 0,
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    validated_at TIMESTAMP,
    experiment_phase TEXT DEFAULT NULL,
    FOREIGN KEY (template_id) REFERENCES templates (id)
);


CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL,
    field_name TEXT NOT NULL,
    original_value TEXT,
    corrected_value TEXT NOT NULL,
    confidence_score REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    used_for_training BOOLEAN DEFAULT 0,
    FOREIGN KEY (document_id) REFERENCES documents (id)
);



CREATE TABLE IF NOT EXISTS strategy_performance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_id INTEGER NOT NULL,
    strategy_type TEXT NOT NULL,
    field_name TEXT,
    accuracy REAL DEFAULT 0.0,
    total_extractions INTEGER DEFAULT 0,
    correct_extractions INTEGER DEFAULT 0,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (template_id) REFERENCES templates(id),
    UNIQUE(template_id, strategy_type, field_name)
);


CREATE INDEX IF NOT EXISTS idx_templates_config_path ON templates(config_path);
CREATE INDEX IF NOT EXISTS idx_templates_field_count ON templates(field_count);
CREATE INDEX IF NOT EXISTS idx_templates_status ON templates(status);

CREATE INDEX IF NOT EXISTS idx_documents_template_id ON documents(template_id);
CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status);
CREATE INDEX IF NOT EXISTS idx_documents_extraction_time_ms ON documents(extraction_time_ms);

CREATE INDEX IF NOT EXISTS idx_feedback_document_id ON feedback(document_id);
CREATE INDEX IF NOT EXISTS idx_feedback_field_name ON feedback(field_name);
CREATE INDEX IF NOT EXISTS idx_feedback_used_for_training ON feedback(used_for_training);
CREATE INDEX IF NOT EXISTS idx_feedback_confidence_score ON feedback(confidence_score);

CREATE INDEX IF NOT EXISTS idx_strategy_performance_template_id ON strategy_performance(template_id);
CREATE INDEX IF NOT EXISTS idx_strategy_performance_strategy_type ON strategy_performance(strategy_type);
CREATE INDEX IF NOT EXISTS idx_strategy_performance_field_name ON strategy_performance(field_name);
CREATE INDEX IF NOT EXISTS idx_strategy_performance_accuracy ON strategy_performance(accuracy);
CREATE INDEX IF NOT EXISTS idx_strategy_performance_total_extractions ON strategy_performance(total_extractions);
CREATE INDEX IF NOT EXISTS idx_strategy_performance_correct_extractions ON strategy_performance(correct_extractions);
