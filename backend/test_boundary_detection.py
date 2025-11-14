#!/usr/bin/env python3
"""
Test script to verify X-boundary detection for kabupaten_daftar field
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from database.db_manager import DatabaseManager
from core.templates.config_loader import get_config_loader
import pdfplumber
import json

# Initialize
db = DatabaseManager('data/app.db')

# Load template config
config_loader = get_config_loader(db_manager=db, template_folder=None)
config = config_loader.load_config(template_id=1, config_path=None)

if not config:
    print('❌ Failed to load config')
    sys.exit(1)

print('✅ Config loaded')
print()

# Get kabupaten_daftar field config
kabupaten_field = config['fields'].get('kabupaten_daftar', {})
if not kabupaten_field:
    print('❌ kabupaten_daftar field not found')
    sys.exit(1)

locations = kabupaten_field.get('locations', [])
if not locations:
    print('❌ No locations found')
    sys.exit(1)

location = locations[0]
context = location.get('context', {})

print('📋 FIELD CONFIG:')
print(f'   Location: X({location["x0"]:.1f}-{location["x1"]:.1f}), Y({location["y0"]:.1f}-{location["y1"]:.1f})')
print(f'   Context:')
print(f'      words_after: {context.get("words_after", [])}')
print(f'      next_field_y: {context.get("next_field_y")}')
print()

# Get X-boundary
words_after = context.get('words_after', [])
next_field_x = None
if words_after and len(words_after) > 0:
    next_field_x = words_after[0].get('x')

print(f'🎯 BOUNDARY DETECTION:')
print(f'   next_field_x: {next_field_x}')
print()

# Get a sample PDF
import glob
pdfs = glob.glob('uploads/*.pdf')
if not pdfs:
    print('❌ No PDFs found')
    sys.exit(1)

pdf_path = pdfs[0]
print(f'📄 Testing with: {pdf_path}')
print()

# Extract words
with pdfplumber.open(pdf_path) as pdf:
    page = pdf.pages[0]
    words = page.extract_words()
    
    # Filter words in kabupaten_daftar area
    marker_x0 = location['x0']
    marker_x1 = location['x1']
    marker_y0 = location['y0']
    marker_y1 = location['y1']
    marker_y_center = (marker_y0 + marker_y1) / 2
    
    # Search area
    x0 = marker_x0 - 50
    y0 = marker_y0 - 10
    x1 = marker_x1 + 400
    y1 = marker_y1 + 10
    
    print(f'🔍 FILTERING WORDS:')
    print(f'   Search area: X({x0:.1f}-{x1:.1f}), Y({y0:.1f}-{y1:.1f})')
    print()
    
    candidate_words = []
    for word in words:
        word_x0 = word.get('x0', 0)
        word_x1 = word.get('x1', 0)
        word_y = word.get('top', 0)
        word_y_center = (word.get('top', 0) + word.get('bottom', 0)) / 2
        word_text = word.get('text', '')
        
        # Basic area check
        if not (word_x0 >= x0 and word_x1 <= x1 and
                word_y >= y0 and word.get('bottom', 0) <= y1):
            continue
        
        # X-boundary check
        if next_field_x:
            if word_x0 >= next_field_x and abs(word_y_center - marker_y_center) < 10:
                print(f'   ❌ "{word_text}" at X={word_x0:.1f}, Y={word_y:.1f} (>= {next_field_x:.1f}) - REJECTED')
                continue
        
        print(f'   ✅ "{word_text}" at X={word_x0:.1f}, Y={word_y:.1f} - ACCEPTED')
        candidate_words.append(word)
    
    print()
    extracted_value = ' '.join(w.get('text', '') for w in candidate_words)
    print(f'📊 RESULT:')
    print(f'   Extracted: "{extracted_value}"')
    print()
    
    # Check if comma is included
    if ',' in extracted_value:
        print('⚠️  WARNING: Comma is included in extraction!')
        print('   This will be removed by post-processing')
    
    # Check if tanggal is included
    if any(c.isdigit() for c in extracted_value):
        print('❌ ERROR: Date is included in extraction!')
        print('   X-boundary detection is NOT working!')
    else:
        print('✅ SUCCESS: No date in extraction')
        print('   X-boundary detection is working!')
