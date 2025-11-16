#!/usr/bin/env python3
"""
Fix approver_id field location

Problem: approver_id label is at x=369 but database has x=153
This causes it to extract surveyor_id instead
"""
import sqlite3

db_path = "data/app.db"

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get current location
cursor.execute("""
    SELECT fl.id, fl.label, fl.x0, fl.y0, fc.field_name
    FROM field_locations fl
    JOIN field_configs fc ON fc.id = fl.field_config_id
    WHERE fc.config_id IN (SELECT id FROM template_configs WHERE template_id = 2)
      AND fc.field_name = 'approver_id'
""")

result = cursor.fetchone()
if result:
    loc_id, label, x0, y0, field_name = result
    print(f"\n📍 Current approver_id location:")
    print(f"   ID: {loc_id}")
    print(f"   Label: {label}")
    print(f"   Position: x={x0}, y={y0}")
    
    # Update to correct position
    # From PDF analysis: ID: at x=369.6, y=675.0
    new_x0 = 369.6
    new_y0 = 675.0
    
    print(f"\n🔧 Updating to correct position:")
    print(f"   New position: x={new_x0}, y={new_y0}")
    
    cursor.execute("""
        UPDATE field_locations
        SET x0 = ?, y0 = ?, x1 = ?, y1 = ?
        WHERE id = ?
    """, (new_x0, new_y0, new_x0 + 50, new_y0 + 12, loc_id))
    
    conn.commit()
    print(f"   ✅ Updated!")
    
    # Also update field_contexts label_position
    cursor.execute("""
        UPDATE field_contexts
        SET label_position = ?
        WHERE field_location_id = ?
    """, (f'{{"x0": {new_x0}, "y0": {new_y0}, "x1": {new_x0 + 50}, "y1": {new_y0 + 12}}}', loc_id))
    
    conn.commit()
    print(f"   ✅ Updated field_contexts!")
else:
    print("❌ approver_id location not found")

conn.close()

print("\n✅ Done!")
