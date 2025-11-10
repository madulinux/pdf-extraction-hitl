CREATE TABLE IF NOT EXISTS training_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_id INTEGER NOT NULL,
    model_path TEXT NOT NULL,
    training_samples INTEGER,
    accuracy REAL,
    precision_score REAL,
    recall_score REAL,
    f1_score REAL,
    trained_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (template_id) REFERENCES templates (id)
);

CREATE INDEX IF NOT EXISTS idx_training_history_template ON training_history(template_id);
CREATE INDEX IF NOT EXISTS idx_training_history_trained_at ON training_history(trained_at);
