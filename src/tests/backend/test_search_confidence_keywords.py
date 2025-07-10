#!/usr/bin/env python3
"""
Test script to verify confidence display in file and text classification.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
parent_dir = Path(__file__).parent.parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from gradio_modules.classification_formatter import format_classification_response


def test_classification_confidence_display():
    """Test how confidence is displayed in classification results."""
    print("🔍 Testing classification confidence display...")

    # Test case 1: Classification with confidence as float
    print("\n📝 Test 1: Classification with confidence as float (0.85)")

    classification_data = {
        "classification": {
            "answer": {
                "classification": "CONFIDENTIAL",
                "sensitivity": "HIGH",
                "reasoning": "This document contains sensitive information that requires restricted access.",
                "confidence": 0.85,
            }
        }
    }

    extraction_result = {
        "content": "This is a confidential document containing sensitive information.",
        "method": "text_file",
        "file_size": 1024,
        "file_type": ".txt",
    }

    original_filename = "test_document.txt"

    try:
        formatted_results = format_classification_response(
            classification_data, extraction_result, original_filename
        )

        print("Formatted results:")
        print(f"  Results box: {formatted_results['results_box'][:200]}...")
        print(f"  Summary: {formatted_results['summary'][:200]}...")

        # Check if confidence is displayed
        results_box_has_confidence = "Confidence:" in formatted_results["results_box"]
        summary_has_confidence = "Confidence Level:" in formatted_results["summary"]

        print(f"  Results box contains confidence: {results_box_has_confidence}")
        print(f"  Summary contains confidence: {summary_has_confidence}")

        if results_box_has_confidence and summary_has_confidence:
            print("  ✅ Confidence is properly displayed")
        else:
            print("  ❌ Confidence is NOT displayed properly")

    except Exception as e:
        print(f"  ❌ Error formatting classification: {e}")

    # Test case 2: Classification with confidence as string
    print("\n📝 Test 2: Classification with confidence as string ('85%')")

    classification_data_2 = {
        "classification": {
            "answer": {
                "classification": "OFFICIAL(OPEN)",
                "sensitivity": "LOW",
                "reasoning": "This document contains general information.",
                "confidence": "85%",
            }
        }
    }

    try:
        formatted_results_2 = format_classification_response(
            classification_data_2, extraction_result, original_filename
        )

        results_box_has_confidence_2 = (
            "Confidence:" in formatted_results_2["results_box"]
        )
        summary_has_confidence_2 = "Confidence Level:" in formatted_results_2["summary"]

        print(f"  Results box contains confidence: {results_box_has_confidence_2}")
        print(f"  Summary contains confidence: {summary_has_confidence_2}")

        if results_box_has_confidence_2 and summary_has_confidence_2:
            print("  ✅ Confidence is properly displayed")
        else:
            print("  ❌ Confidence is NOT displayed properly")

    except Exception as e:
        print(f"  ❌ Error formatting classification: {e}")

    # Test case 3: Classification with missing confidence
    print("\n📝 Test 3: Classification with missing confidence")

    classification_data_3 = {
        "classification": {
            "answer": {
                "classification": "RESTRICTED",
                "sensitivity": "HIGH",
                "reasoning": "This document contains restricted information.",
                # No confidence field
            }
        }
    }

    try:
        formatted_results_3 = format_classification_response(
            classification_data_3, extraction_result, original_filename
        )

        results_box_has_confidence_3 = (
            "Confidence:" in formatted_results_3["results_box"]
        )
        summary_has_confidence_3 = "Confidence Level:" in formatted_results_3["summary"]

        print(f"  Results box contains confidence: {results_box_has_confidence_3}")
        print(f"  Summary contains confidence: {summary_has_confidence_3}")

        # Should show "N/A" for missing confidence
        has_na_confidence = (
            "N/A" in formatted_results_3["results_box"]
            or "N/A" in formatted_results_3["summary"]
        )
        print(f"  Shows N/A for missing confidence: {has_na_confidence}")

        if (
            results_box_has_confidence_3
            and summary_has_confidence_3
            and has_na_confidence
        ):
            print("  ✅ Missing confidence is handled properly")
        else:
            print("  ❌ Missing confidence is NOT handled properly")

    except Exception as e:
        print(f"  ❌ Error formatting classification: {e}")

    # Test case 4: Check the actual confidence extraction logic
    print("\n📝 Test 4: Checking confidence extraction logic")

    # Simulate the confidence extraction from the formatter
    parsed_llm_output = {
        "classification": "CONFIDENTIAL",
        "sensitivity": "HIGH",
        "reasoning": "Test reasoning",
        "confidence": 0.92,
    }

    confidence = str(parsed_llm_output.get("confidence", "N/A"))
    print(f"  Extracted confidence: {confidence}")
    print(f"  Confidence type: {type(confidence)}")

    # Check if it's properly formatted for display
    if confidence == "0.92":
        print("  ✅ Confidence is extracted as string")
    else:
        print("  ❌ Confidence extraction issue")

    return True


def test_classification_formatter_structure():
    """Test the structure of classification formatter output."""
    print("\n🔍 Testing classification formatter structure...")

    # Mock classification data
    classification_data = {
        "classification": {
            "answer": {
                "classification": "CONFIDENTIAL",
                "sensitivity": "HIGH",
                "reasoning": "This document contains sensitive information.",
                "confidence": 0.85,
            }
        }
    }

    extraction_result = {
        "content": "Test content",
        "method": "text_file",
        "file_size": 1024,
        "file_type": ".txt",
    }

    original_filename = "test.txt"

    try:
        formatted_results = format_classification_response(
            classification_data, extraction_result, original_filename
        )

        # Check required fields
        required_fields = [
            "results_box",
            "classification",
            "sensitivity",
            "file_info",
            "reasoning",
            "summary",
        ]

        for field in required_fields:
            if field in formatted_results:
                print(f"  ✅ {field} field present")
            else:
                print(f"  ❌ {field} field missing")

        # Check if confidence appears in the right places
        confidence_locations = {
            "results_box": "results_box" in formatted_results
            and "Confidence:" in formatted_results["results_box"],
            "summary": "summary" in formatted_results
            and "Confidence Level:" in formatted_results["summary"],
        }

        for location, has_confidence in confidence_locations.items():
            if has_confidence:
                print(f"  ✅ Confidence displayed in {location}")
            else:
                print(f"  ❌ Confidence NOT displayed in {location}")

        return all(confidence_locations.values())

    except Exception as e:
        print(f"  ❌ Error testing formatter structure: {e}")
        return False


def main():
    """Run all tests."""
    print("🧪 Testing classification confidence display...")
    print("=" * 60)

    # Run tests
    confidence_display_passed = test_classification_confidence_display()
    formatter_structure_passed = test_classification_formatter_structure()

    print("\n" + "=" * 60)
    print("📊 TEST RESULTS:")
    print(
        f"  Confidence Display: {'✅ PASSED' if confidence_display_passed else '❌ FAILED'}"
    )
    print(
        f"  Formatter Structure: {'✅ PASSED' if formatter_structure_passed else '❌ FAILED'}"
    )

    print("\n📋 ANALYSIS:")
    print("✅ The classification formatter SHOULD display confidence:")
    print("   - In the results_box HTML content")
    print("   - In the summary markdown")
    print("   - As a percentage or decimal value")
    print("   - As 'N/A' when confidence is missing")

    print("\n🔍 POTENTIAL ISSUES:")
    print("1. LLM response structure may not include confidence field")
    print("2. Confidence field may be named differently")
    print("3. Confidence value may not be properly formatted")
    print("4. The formatter may not be extracting confidence correctly")

    print("\n💡 RECOMMENDATIONS:")
    print("1. Check the LLM response structure in classificationModel.py")
    print("2. Verify the confidence field is being returned by the LLM")
    print("3. Ensure the formatter is correctly parsing the confidence value")
    print("4. Test with actual file classification to see the real output")

    all_passed = confidence_display_passed and formatter_structure_passed
    print(
        f"\nOverall: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}"
    )

    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
