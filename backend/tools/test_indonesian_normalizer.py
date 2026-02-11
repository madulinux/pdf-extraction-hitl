"""
Test Indonesian Text Normalizer

Test word segmentation for Indonesian language
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.extraction.text_normalizer import TextNormalizer, get_normalizer
from core.extraction.language_dictionaries import get_supported_languages


def test_indonesian_segmentation():
    """Test Indonesian word segmentation"""
    normalizer = TextNormalizer(language='id')
    
    test_cases = [
        # (input, expected_contains)
        ("konferensikadang", ["konferensi", "kadang"]),
        ("kebijakansisi", ["kebijakan", "sisi"]),
        ("suaramenyarankan", ["suara", "menyarankan"]),
        ("malamkhusus", ["malam", "khusus"]),
        ("senjatadetik", ["senjata", "detik"]),
        
        # Already correct text
        ("konferensi kadang", ["konferensi", "kadang"]),
        ("nama lengkap", ["nama", "lengkap"]),
        ("alamat rumah", ["alamat", "rumah"]),
    ]
    
    print("=" * 80)
    print("INDONESIAN WORD SEGMENTATION TESTS")
    print("=" * 80)
    
    passed = 0
    failed = 0
    
    for i, (input_text, expected_words) in enumerate(test_cases, 1):
        result = normalizer.segment_concatenated_text(input_text)
        
        # Check if all expected words are in result
        all_found = all(word.lower() in result.lower() for word in expected_words)
        
        status = "✅ PASS" if all_found else "❌ FAIL"
        if all_found:
            passed += 1
        else:
            failed += 1
        
        print(f"\nTest {i}: {status}")
        print(f"  Input:    '{input_text}'")
        print(f"  Output:   '{result}'")
        print(f"  Expected: {expected_words}")
        
        if not all_found:
            missing = [w for w in expected_words if w.lower() not in result.lower()]
            print(f"  Missing:  {missing}")
    
    print("\n" + "=" * 80)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 80)
    
    return failed == 0


def test_multi_language():
    """Test multiple languages"""
    print("\n" + "=" * 80)
    print("MULTI-LANGUAGE SUPPORT TEST")
    print("=" * 80)
    
    # English
    en_normalizer = get_normalizer('en')
    en_text = "conferencesometimes"
    en_result = en_normalizer.segment_concatenated_text(en_text)
    print(f"\n✅ English:")
    print(f"  Input:  '{en_text}'")
    print(f"  Output: '{en_result}'")
    
    # Indonesian
    id_normalizer = get_normalizer('id')
    id_text = "konferensikadang"
    id_result = id_normalizer.segment_concatenated_text(id_text)
    print(f"\n✅ Indonesian:")
    print(f"  Input:  '{id_text}'")
    print(f"  Output: '{id_result}'")
    
    # Check cache works
    en_normalizer2 = get_normalizer('en')
    print(f"\n✅ Cache test:")
    print(f"  Same instance: {en_normalizer is en_normalizer2}")


def test_custom_dictionary():
    """Test adding custom words"""
    print("\n" + "=" * 80)
    print("CUSTOM DICTIONARY TEST")
    print("=" * 80)
    
    normalizer = TextNormalizer(language='en')
    
    # Before adding custom words
    text = "universityindonesia"
    result_before = normalizer.segment_concatenated_text(text)
    print(f"\nBefore adding custom words:")
    print(f"  Input:  '{text}'")
    print(f"  Output: '{result_before}'")
    
    # Add custom words
    normalizer.add_words({'indonesia', 'university'})
    
    # After adding custom words
    result_after = normalizer.segment_concatenated_text(text)
    print(f"\nAfter adding custom words:")
    print(f"  Input:  '{text}'")
    print(f"  Output: '{result_after}'")


def test_supported_languages():
    """Test supported languages"""
    print("\n" + "=" * 80)
    print("SUPPORTED LANGUAGES")
    print("=" * 80)
    
    languages = get_supported_languages()
    print(f"\nSupported languages: {languages}")
    
    for lang in languages:
        normalizer = get_normalizer(lang)
        print(f"  ✅ {lang}: {len(normalizer._common_words)} words in dictionary")


def main():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("INDONESIAN TEXT NORMALIZER TEST SUITE")
    print("=" * 80)
    
    # Run tests
    test_supported_languages()
    test_indonesian_segmentation()
    test_multi_language()
    test_custom_dictionary()
    
    print("\n" + "=" * 80)
    print("ALL TESTS COMPLETED")
    print("=" * 80)


if __name__ == "__main__":
    main()
