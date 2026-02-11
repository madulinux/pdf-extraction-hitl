"""
Test Text Normalizer

Test the text normalization and word segmentation functionality
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.extraction.text_normalizer import TextNormalizer


def test_word_segmentation():
    """Test word segmentation on concatenated text"""
    normalizer = TextNormalizer()
    
    test_cases = [
        # (input, expected_contains)
        ("conferencesometimes", ["conference", "sometimes"]),
        ("soundsuggest", ["sound", "suggest"]),
        ("Everybody hear conferencesometimes policy side soundsuggest tonight particular gunsecond", 
         ["conference", "sometimes", "sound", "suggest"]),
        ("policyside", ["policy", "side"]),
        ("tonightparticular", ["tonight", "particular"]),
        ("gunsecond", ["gun", "second"]),
        
        # Already correct text (should remain unchanged)
        ("conference sometimes", ["conference", "sometimes"]),
        ("John Doe", ["John", "Doe"]),
        ("123 Main Street", ["123", "Main", "Street"]),
    ]
    
    print("=" * 80)
    print("WORD SEGMENTATION TESTS")
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


def test_normalization():
    """Test full text normalization"""
    normalizer = TextNormalizer()
    
    test_cases = [
        "Everybody hear conferencesometimes policy side soundsuggest tonight particular gunsecond.",
        "conferencesometimes",
        "This is normal text",
        "verylongwordwithoutspaces",
    ]
    
    print("\n" + "=" * 80)
    print("FULL NORMALIZATION TESTS")
    print("=" * 80)
    
    for i, text in enumerate(test_cases, 1):
        result = normalizer.normalize_text(text)
        
        print(f"\nTest {i}:")
        print(f"  Input:  '{text}'")
        print(f"  Output: '{result}'")
        print(f"  Needs normalization: {normalizer.should_normalize(text)}")


def test_edge_cases():
    """Test edge cases"""
    normalizer = TextNormalizer()
    
    test_cases = [
        "",  # Empty string
        "a",  # Single character
        "ab",  # Two characters
        "   ",  # Only spaces
        "123",  # Numbers only
        "!@#$",  # Special characters
        "word1word2word3word4word5",  # Multiple concatenated words
    ]
    
    print("\n" + "=" * 80)
    print("EDGE CASE TESTS")
    print("=" * 80)
    
    for i, text in enumerate(test_cases, 1):
        try:
            result = normalizer.normalize_text(text)
            print(f"\nTest {i}: ✅ No error")
            print(f"  Input:  '{text}'")
            print(f"  Output: '{result}'")
        except Exception as e:
            print(f"\nTest {i}: ❌ Error")
            print(f"  Input:  '{text}'")
            print(f"  Error:  {e}")


def main():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("TEXT NORMALIZER TEST SUITE")
    print("=" * 80)
    
    # Run tests
    test_word_segmentation()
    test_normalization()
    test_edge_cases()
    
    print("\n" + "=" * 80)
    print("ALL TESTS COMPLETED")
    print("=" * 80)


if __name__ == "__main__":
    main()
