#!/usr/bin/env python3
"""
Test script to verify Mermaid string enclosure functionality.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
parent_dir = Path(__file__).parent.parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from backend.markdown_formatter import (
    format_markdown,
    _enclose_strings_in_mermaid_diagrams,
    _process_mermaid_line,
)


def test_mermaid_string_enclosure():
    """Test Mermaid string enclosure functionality."""
    print("🔍 Testing Mermaid string enclosure...")

    test_cases = [
        # Test case 1: Basic node labels
        {
            "input": "graph TD\n    A[Start] --> B[Process]\n    B --> C[End]",
            "expected_contains": 'A["Start"]',
            "description": "Basic node labels should be enclosed in quotes",
        },
        # Test case 2: Edge labels
        {
            "input": "graph TD\n    A -->|Yes| B\n    A -->|No| C",
            "expected_contains": '-->|"Yes"|',
            "description": "Edge labels should be enclosed in quotes",
        },
        # Test case 3: Already quoted content
        {
            "input": 'graph TD\n    A["Already Quoted"] --> B[Not Quoted]',
            "expected_contains": 'A["Already Quoted"]',
            "description": "Already quoted content should remain unchanged",
        },
        # Test case 4: Mixed content
        {
            "input": "graph TD\n    A[Start] -->|Begin| B[Process Step]\n    B -->|Continue| C[End]",
            "expected_contains": 'A["Start"]',
            "description": "Mixed content should be properly quoted",
        },
        # Test case 5: Special characters (should be skipped)
        {
            "input": "graph TD\n    A[<script>alert('xss')</script>] --> B[Safe]",
            "expected_contains": "A[<script>alert('xss')</script>]",
            "description": "Content with special characters should be skipped",
        },
        # Test case 6: Different arrow types
        {
            "input": "graph TD\n    A -->|Normal| B\n    A -.->|Dotted| C\n    A ==>|Thick| D\n    A =>|Fat| E",
            "expected_contains": '-->|"Normal"|',
            "description": "Different arrow types should be handled",
        },
        # Test case 7: Empty labels
        {
            "input": "graph TD\n    A[] --> B[Valid]\n    C -->| | D",
            "expected_contains": 'B["Valid"]',
            "description": "Empty labels should be skipped",
        },
        # Test case 8: Complex diagram
        {
            "input": """graph TD
    A[User Input] -->|Submit| B[Validation]
    B -->|Valid| C[Process]
    B -->|Invalid| D[Error Message]
    C -->|Success| E[Result]
    C -->|Failure| F[Retry]""",
            "expected_contains": 'A["User Input"]',
            "description": "Complex diagram should be properly quoted",
        },
    ]

    passed = 0
    total = len(test_cases)

    for i, test_case in enumerate(test_cases, 1):
        print(f"  📝 Test {i}: {test_case['description']}")

        try:
            # Test the individual function
            result = _enclose_strings_in_mermaid_diagrams(test_case["input"])

            if test_case["expected_contains"] in result:
                print("    ✅ PASS: Found expected content")
                passed += 1
            else:
                print(
                    f"    ❌ FAIL: Expected '{test_case['expected_contains']}' not found"
                )
                print(f"    Result: {result}")

        except Exception as e:
            print(f"    ❌ FAIL: Exception occurred: {e}")

    print(f"📊 String enclosure results: {passed}/{total} tests passed")
    return passed == total


def test_mermaid_line_processing():
    """Test individual line processing functionality."""
    print("\n🔍 Testing Mermaid line processing...")

    test_cases = [
        # Test individual lines
        ("A[Start]", 'A["Start"]', "Simple node label"),
        ("A -->|Yes| B", 'A -->|"Yes"| B', "Edge label"),
        ('A["Already Quoted"]', 'A["Already Quoted"]', "Already quoted content"),
        (
            "A[<script>alert('xss')</script>]",
            "A[<script>alert('xss')</script>]",
            "Special characters",
        ),
        ("A[]", "A[]", "Empty label"),
        ("A --> B", "A --> B", "No label"),
        ("A -.->|Dotted| B", 'A -.->|"Dotted"| B', "Dotted arrow with label"),
        ("A ==>|Thick| B", 'A ==>|"Thick"| B', "Thick arrow with label"),
        ("A =>|Fat| B", 'A =>|"Fat"| B', "Fat arrow with label"),
    ]

    passed = 0
    total = len(test_cases)

    for i, (input_line, expected, description) in enumerate(test_cases, 1):
        print(f"  📝 Test {i}: {description}")

        try:
            result = _process_mermaid_line(input_line)

            if result == expected:
                print("    ✅ PASS: Line processed correctly")
                passed += 1
            else:
                print(f"    ❌ FAIL: Expected '{expected}', got '{result}'")

        except Exception as e:
            print(f"    ❌ FAIL: Exception occurred: {e}")

    print(f"📊 Line processing results: {passed}/{total} tests passed")
    return passed == total


def test_full_markdown_formatting():
    """Test full markdown formatting with Mermaid string enclosure."""
    print("\n🔍 Testing full markdown formatting...")

    test_cases = [
        {
            "input": "Here's a diagram:\n```mermaid\ngraph TD\n    A[Start] --> B[Process]\n    B --> C[End]\n```",
            "expected_contains": 'A["Start"]',
            "description": "Full markdown formatting should include string enclosure",
        },
        {
            "input": "```mermaid\ngraph TD\n    A[User Input] -->|Submit| B[Validation]\n```",
            "expected_contains": 'A["User Input"]',
            "description": "Mermaid block in markdown should be processed",
        },
    ]

    passed = 0
    total = len(test_cases)

    for i, test_case in enumerate(test_cases, 1):
        print(f"  📝 Test {i}: {test_case['description']}")

        try:
            result = format_markdown(test_case["input"])

            if test_case["expected_contains"] in result:
                print("    ✅ PASS: Found expected content")
                passed += 1
            else:
                print(
                    f"    ❌ FAIL: Expected '{test_case['expected_contains']}' not found"
                )
                print(f"    Result: {result[:200]}...")

        except Exception as e:
            print(f"    ❌ FAIL: Exception occurred: {e}")

    print(f"📊 Full formatting results: {passed}/{total} tests passed")
    return passed == total


def main():
    """Run all tests."""
    print("🧪 Running Mermaid string enclosure tests...")
    print("=" * 60)

    # Run individual function tests
    string_enclosure_passed = test_mermaid_string_enclosure()
    line_processing_passed = test_mermaid_line_processing()
    full_formatting_passed = test_full_markdown_formatting()

    print("\n" + "=" * 60)
    print("📊 FINAL RESULTS:")
    print(
        f"  String Enclosure: {'✅ PASSED' if string_enclosure_passed else '❌ FAILED'}"
    )
    print(
        f"  Line Processing: {'✅ PASSED' if line_processing_passed else '❌ FAILED'}"
    )
    print(
        f"  Full Formatting: {'✅ PASSED' if full_formatting_passed else '❌ FAILED'}"
    )

    all_passed = (
        string_enclosure_passed and line_processing_passed and full_formatting_passed
    )
    print(
        f"\nOverall: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}"
    )

    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
