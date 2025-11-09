"""
Migration: Create strategy_performance table
Tracks historical accuracy of each extraction strategy per template
"""

def upgrade(conn):
    """Create strategy_performance table"""
    cursor = conn.cursor()
    
    cursor.execute('''
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
        )
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_strategy_performance_template ON strategy_performance(template_id)
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_strategy_performance_strategy ON strategy_performance(strategy_type)
    ''')
    
    conn.commit()
    print("✅ Created strategy_performance table")

def downgrade(conn):
    """Drop strategy_performance table"""
    cursor = conn.cursor()
    cursor.execute('DROP TABLE IF EXISTS strategy_performance')
    conn.commit()
    print("✅ Dropped strategy_performance table")
