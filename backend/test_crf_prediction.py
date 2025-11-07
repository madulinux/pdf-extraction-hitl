#!/usr/bin/env python3
"""
Test CRF prediction on a new PDF
"""

import sys
import pdfplumber
import joblib
from core.learning.learner import AdaptiveLearner

def test_prediction(pdf_path: str, model_path: str):
    """Test CRF prediction on a PDF"""
    
    print(f"\n{'='*60}")
    print(f"🔍 TEST CRF PREDICTION")
    print(f"{'='*60}\n")
    
    print(f"PDF: {pdf_path}")
    print(f"Model: {model_path}")
    print()
    
    # Load model
    model = joblib.load(model_path)
    print(f"✅ Model loaded")
    print(f"Model classes: {model.classes_}")
    print()
    
    # Extract words
    with pdfplumber.open(pdf_path) as pdf:
        words = []
        for page in pdf.pages:
            page_words = page.extract_words(x_tolerance=3, y_tolerance=3)
            words.extend(page_words)
    
    print(f"📝 Total words: {len(words)}")
    print(f"Sample words (first 20):")
    for i, word in enumerate(words[:20]):
        print(f"  {i}: {word['text']}")
    print()
    
    # Extract features using AdaptiveLearner method
    learner = AdaptiveLearner()
    features = []
    for i, word in enumerate(words):
        word_features = learner._extract_word_features(word, words, i)
        features.append(word_features)
    
    print(f"✅ Features extracted: {len(features)}")
    print(f"Sample feature keys:")
    if features:
        for key in sorted(features[0].keys())[:10]:
            print(f"  - {key}: {features[0][key]}")
    print()
    
    # Predict
    predictions = model.predict([features])[0]
    
    print(f"{'='*60}")
    print(f"🤖 PREDICTIONS")
    print(f"{'='*60}\n")
    
    from collections import Counter
    pred_counts = Counter(predictions)
    print(f"Label distribution:")
    for label, count in sorted(pred_counts.items()):
        print(f"  {label}: {count}")
    print()
    
    # Show labeled tokens
    print(f"Labeled tokens (non-O):")
    for i, (word, label) in enumerate(zip(words, predictions)):
        if label != 'O':
            print(f"  {i}: '{word['text']}' → {label}")
    print()
    
    # Extract fields
    print(f"{'='*60}")
    print(f"📊 EXTRACTED FIELDS")
    print(f"{'='*60}\n")
    
    # Group by field
    fields = {}
    current_field = None
    current_tokens = []
    
    for i, (word, label) in enumerate(zip(words, predictions)):
        if label.startswith('B-'):
            # Save previous field
            if current_field and current_tokens:
                fields[current_field] = ' '.join(current_tokens)
            # Start new field
            current_field = label[2:]  # Remove 'B-'
            current_tokens = [word['text']]
        elif label.startswith('I-') and current_field:
            # Continue current field
            current_tokens.append(word['text'])
        elif label == 'O':
            # Save previous field
            if current_field and current_tokens:
                fields[current_field] = ' '.join(current_tokens)
            current_field = None
            current_tokens = []
    
    # Save last field
    if current_field and current_tokens:
        fields[current_field] = ' '.join(current_tokens)
    
    if fields:
        for field_name, value in fields.items():
            print(f"  {field_name}: {value}")
    else:
        print("  ❌ No fields extracted!")
    
    print()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_crf_prediction.py <pdf_path> [model_path]")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    model_path = sys.argv[2] if len(sys.argv) > 2 else "models/template_1_model.joblib"
    
    test_prediction(pdf_path, model_path)
