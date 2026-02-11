"""
Test Whitespace Tolerance in Extraction Comparison

Verify that the normalize_whitespace function correctly handles
various whitespace differences in extraction results.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from experiments.run_adaptive import normalize_whitespace


def test_whitespace_normalization():
    """Test whitespace normalization function"""
    
    test_cases = [
        # (input, expected_output, description)
        ("John Doe", "John Doe", "Normal text - no change"),
        ("John  Doe", "John Doe", "Multiple spaces → single space"),
        ("John\tDoe", "John Doe", "Tab → space"),
        ("John\nDoe", "John Doe", "Newline → space"),
        ("  John Doe  ", "John Doe", "Leading/trailing spaces removed"),
        ("John   \t  Doe", "John Doe", "Mixed whitespace normalized"),
        ("", "", "Empty string"),
        ("   ", "", "Only whitespace → empty"),
        ("John\r\nDoe", "John Doe", "Windows newline → space"),
        ("John    \n\n    Doe", "John Doe", "Multiple newlines + spaces"),
    ]
    
    print("=" * 80)
    print("WHITESPACE NORMALIZATION TESTS")
    print("=" * 80)
    
    passed = 0
    failed = 0
    
    for i, (input_text, expected, description) in enumerate(test_cases, 1):
        result = normalize_whitespace(input_text)
        
        status = "✅ PASS" if result == expected else "❌ FAIL"
        if result == expected:
            passed += 1
        else:
            failed += 1
        
        print(f"\nTest {i}: {status}")
        print(f"  Description: {description}")
        print(f"  Input:       '{input_text}' (repr: {repr(input_text)})")
        print(f"  Expected:    '{expected}'")
        print(f"  Got:         '{result}'")
        
        if result != expected:
            print(f"  ❌ MISMATCH!")
    
    print("\n" + "=" * 80)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 80)
    
    return failed == 0


def test_extraction_comparison():
    """Test extraction comparison with whitespace tolerance"""
    
    comparison_cases = [
        # (extracted, ground_truth, should_match, description)
        ("John Doe", "John Doe", True, "Exact match"),
        ("John  Doe", "John Doe", True, "Extra space in extracted"),
        ("John Doe", "John  Doe", True, "Extra space in ground truth"),
        ("John\tDoe", "John Doe", True, "Tab in extracted"),
        ("John Doe", "John\tDoe", True, "Tab in ground truth"),
        ("John\nDoe", "John Doe", True, "Newline in extracted"),
        ("  John Doe  ", "John Doe", True, "Leading/trailing spaces"),
        ("John Doe", "Jane Doe", False, "Different content"),
        ("John", "John Doe", False, "Missing word"),
        ("", "", True, "Both empty"),
        ("   ", "", True, "Whitespace vs empty"),
    ]
    
    print("\n" + "=" * 80)
    print("EXTRACTION COMPARISON TESTS")
    print("=" * 80)
    
    passed = 0
    failed = 0
    
    for i, (extracted, ground_truth, should_match, description) in enumerate(comparison_cases, 1):
        extracted_norm = normalize_whitespace(extracted)
        gt_norm = normalize_whitespace(ground_truth)
        
        matches = (extracted_norm == gt_norm)
        
        status = "✅ PASS" if matches == should_match else "❌ FAIL"
        if matches == should_match:
            passed += 1
        else:
            failed += 1
        
        print(f"\nTest {i}: {status}")
        print(f"  Description:   {description}")
        print(f"  Extracted:     '{extracted}' → '{extracted_norm}'")
        print(f"  Ground Truth:  '{ground_truth}' → '{gt_norm}'")
        print(f"  Should Match:  {should_match}")
        print(f"  Actually:      {matches}")
        
        if matches != should_match:
            print(f"  ❌ UNEXPECTED RESULT!")
    
    print("\n" + "=" * 80)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 80)
    
    return failed == 0


def test_real_world_examples():
    """Test with real-world extraction examples"""
    
    print("\n" + "=" * 80)
    print("REAL-WORLD EXAMPLES")
    print("=" * 80)
    
    examples = [
        {
            "field": "full_name",
            "extracted": "John   Doe",
            "ground_truth": "John Doe",
            "description": "Extra spaces from OCR"
        },
        {
            "field": "address",
            "extracted": "123 Main Street\nApt 4B",
            "ground_truth": "123 Main Street Apt 4B",
            "description": "Newline in address"
        },
        {
            "field": "city",
            "extracted": "New  York",
            "ground_truth": "New York",
            "description": "Double space in city name"
        },
        {
            "field": "description",
            "extracted": "This is a\tlong description",
            "ground_truth": "This is a long description",
            "description": "Tab character in text"
        },
    ]
    
    for i, example in enumerate(examples, 1):
        extracted_norm = normalize_whitespace(example["extracted"])
        gt_norm = normalize_whitespace(example["ground_truth"])
        
        matches = (extracted_norm == gt_norm)
        
        print(f"\nExample {i}: {example['field']}")
        print(f"  Description:   {example['description']}")
        print(f"  Extracted:     '{example['extracted']}'")
        print(f"  Ground Truth:  '{example['ground_truth']}'")
        print(f"  Normalized:    '{extracted_norm}' vs '{gt_norm}'")
        print(f"  Match:         {'✅ YES' if matches else '❌ NO'}")


def main():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("WHITESPACE TOLERANCE TEST SUITE")
    print("=" * 80)
    
    # Run tests
    test1_passed = test_whitespace_normalization()
    test2_passed = test_extraction_comparison()
    test_real_world_examples()
    
    print("\n" + "=" * 80)
    print("OVERALL RESULTS")
    print("=" * 80)
    print(f"Normalization Tests: {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"Comparison Tests:    {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    print("=" * 80)
    
    if test1_passed and test2_passed:
        print("\n✅ All tests passed! Whitespace tolerance is working correctly.")
        return 0
    else:
        print("\n❌ Some tests failed. Please review the output above.")
        return 1


if __name__ == "__main__":
    exit(main())
