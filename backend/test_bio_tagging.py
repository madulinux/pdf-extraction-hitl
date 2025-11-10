#!/usr/bin/env python3
"""
Test BIO tagging for event_location field
"""

from database.db_manager import DatabaseManager
from core.learning.learner import AdaptiveLearner
import pdfplumber

# Get feedback for event_location
db = DatabaseManager()
feedback = db.execute_query('''
    SELECT f.*, d.file_path 
    FROM feedback f
    JOIN documents d ON f.document_id = d.id
    WHERE f.field_name = 'event_location'
      AND f.document_id = 257
    LIMIT 1
''')[0]

print(f"📄 Document ID: {feedback['document_id']}")
print(f"🏷️  Field: {feedback['field_name']}")
print(f"📝 Original: {feedback['original_value'][:60]}")
print(f"✅ Corrected: {feedback['corrected_value'][:60]}")
print()

# Extract words from PDF
pdf_path = feedback['file_path']
with pdfplumber.open(pdf_path) as pdf:
    page = pdf.pages[0]
    words = page.extract_words()

print(f"📚 Total words in PDF: {len(words)}")
print()

# Test sequence matching
learner = AdaptiveLearner()
corrected_value = feedback['corrected_value']
corrected_tokens = corrected_value.split()

print(f"🎯 Target tokens ({len(corrected_tokens)}): {corrected_tokens[:10]}")
print()

# Find matching sequence
word_texts = [w['text'] for w in words]
matched_indices = learner._find_best_sequence_match(word_texts, corrected_tokens)

print(f"✅ Matched indices: {matched_indices}")
print(f"📍 Matched words: {[word_texts[i] for i in matched_indices if i < len(word_texts)]}")
print()

# Check if "Jalan" and "Rungkut" are in matched indices
print("🔍 Checking specific words:")
for i, word in enumerate(words):
    if word['text'] in ['Jalan', 'Rungkut', 'Industri', 'No.', '846']:
        in_match = "✅" if i in matched_indices else "❌"
        print(f"  {in_match} [{i}] {word['text']}")
