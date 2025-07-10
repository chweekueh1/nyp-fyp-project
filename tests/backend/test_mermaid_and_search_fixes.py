#!/usr/bin/env python3
"""
Test script to verify Mermaid syntax validation and search result highlighting improvements.
"""

import sys
import asyncio
from pathlib import Path

# Add parent directory to path for imports
parent_dir = Path(__file__).parent.parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from backend.chat import (
    format_search_results,
    search_chat_history,
    _get_chat_metadata_cache_internal,
)
from backend.markdown_formatter import format_markdown


def test_mermaid_syntax_validation():
    """Test Mermaid syntax validation and sanitization."""
    print("🔍 Testing Mermaid syntax validation...")

    test_cases = [
        # Valid Mermaid diagram
        {
            "input": "Here's a flowchart:\n```mermaid\ngraph TD\n    A[Start] --> B[Process]\n    B --> C[End]\n```",
            "expected_contains": "\n\n```mermaid\n",
            "description": "Valid flowchart should have extra newlines for Markdown",
        },
        # Missing directive
        {
            "input": "Here's a diagram:\n```mermaid\nA[Start] --> B[End]\n```",
            "expected_contains": "\n\n```mermaid\nflowchart TD\n",
            "description": "Missing directive - should add flowchart TD with extra newlines",
        },
        # Invalid characters
        {
            "input": "Here's a diagram:\n```mermaid\ngraph TD\n    A[<script>alert('xss')</script>] --> B[End]\n```",
            "expected_contains": "&lt;script&gt;",
            "description": "HTML entities should be escaped",
        },
        # Empty diagram
        {
            "input": "Here's an empty diagram:\n```mermaid\n\n```",
            "expected_contains": "\n\n```mermaid\nflowchart TD\n    A[Invalid Diagram]",
            "description": "Empty diagram should show error message with extra newlines",
        },
        # No Mermaid blocks
        {
            "input": "This is just regular text with no diagrams.",
            "expected_contains": "regular text",
            "description": "Text without Mermaid should be unchanged",
        },
        # Multiple diagrams
        {
            "input": "First diagram:\n```mermaid\ngraph TD\n    A --> B\n```\nSecond diagram:\n```mermaid\nflowchart LR\n    C --> D\n```",
            "expected_contains": "\n\n```mermaid\n",
            "description": "Multiple diagrams should all have extra newlines",
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

    print(f"📊 Mermaid validation results: {passed}/{total} tests passed")
    return passed == total


def test_search_result_highlighting():
    """Test search result highlighting functionality."""
    print("🔍 Testing search result highlighting...")

    # Create test search results
    test_results = [
        {
            "chat_id": "test_chat_1",
            "chat_name": "Test Chat 1",
            "message_type": "user",
            "content": "Hello, I need help with data security classifications.",
            "similarity_score": 0.85,
        },
        {
            "chat_id": "test_chat_2",
            "chat_name": "Test Chat 2",
            "message_type": "bot",
            "content": "I can help you with data security. Data classification is important for protecting sensitive information.",
            "similarity_score": 0.92,
        },
    ]

    test_cases = [
        {
            "query": "data",
            "expected_highlights": ["**data**"],
            "description": "Highlight 'data' in content",
        },
        {
            "query": "security",
            "expected_highlights": ["**security**"],
            "description": "Highlight 'security' in content",
        },
        {
            "query": "classification",
            "expected_highlights": ["**classification**"],
            "description": "Highlight 'classification' in content",
        },
        {
            "query": "nonexistent",
            "expected_highlights": [],
            "description": "No highlights for non-existent term",
        },
    ]

    passed = 0
    total = len(test_cases)

    for i, test_case in enumerate(test_cases, 1):
        print(f"  📝 Test {i}: {test_case['description']}")

        try:
            result = format_search_results(
                test_results, test_case["query"], include_similarity=True
            )

            # Check if expected highlights are present
            highlights_found = 0
            for expected_highlight in test_case["expected_highlights"]:
                if expected_highlight in result:
                    highlights_found += 1

            if highlights_found == len(test_case["expected_highlights"]):
                print(f"    ✅ PASS: Found {highlights_found} expected highlights")
                passed += 1
            else:
                print(
                    f"    ❌ FAIL: Expected {len(test_case['expected_highlights'])} highlights, found {highlights_found}"
                )
                print(f"    Result preview: {result[:300]}...")

        except Exception as e:
            print(f"    ❌ FAIL: Exception occurred: {e}")

    print(f"📊 Search highlighting results: {passed}/{total} tests passed")
    return passed == total


def test_search_with_highlighting():
    """Test the complete search functionality with highlighting."""
    print("🔍 Testing complete search with highlighting...")

    username = "test_search_highlight"

    # Create test chat data
    test_chat_id = "test_search_highlight_123"
    test_chat_data = {
        "name": "Test Search Chat",
        "history": [
            [
                "Can you help me with data security?",
                "Yes, I can help you with data security classifications. Data protection is crucial for sensitive information.",
            ],
            [
                "What about classification levels?",
                "There are several classification levels: Official (Open), Official (Closed), Restricted, Confidential, Secret, and Top Secret.",
            ],
            [
                "How do I classify documents?",
                "To classify documents, you need to assess the sensitivity of the information and apply the appropriate security level.",
            ],
        ],
    }

    # Add test data to cache
    internal_cache = _get_chat_metadata_cache_internal()
    internal_cache[username] = {test_chat_id: test_chat_data}

    print(f"✅ Added test data: {len(test_chat_data['history'])} messages")

    test_queries = [
        ("data", "Should find 'data' in multiple messages"),
        ("security", "Should find 'security' in bot responses"),
        ("classification", "Should find 'classification' in bot responses"),
        ("levels", "Should find 'levels' in bot response"),
        ("nonexistent", "Should find no results"),
    ]

    passed = 0
    total = len(test_queries)

    for query, description in test_queries:
        print(f"  📝 Testing query '{query}': {description}")

        try:
            results, status = search_chat_history(query, username)

            if query == "nonexistent":
                if len(results) == 0:
                    print("    ✅ PASS: No results found as expected")
                    passed += 1
                else:
                    print(f"    ❌ FAIL: Expected no results, found {len(results)}")
            else:
                if len(results) > 0:
                    # Check if highlighting is working
                    formatted_results = format_search_results(
                        results, query, include_similarity=True
                    )
                    if f"**{query}**" in formatted_results:
                        print(
                            f"    ✅ PASS: Found {len(results)} results with highlighting"
                        )
                        passed += 1
                    else:
                        print(
                            f"    ❌ FAIL: Found {len(results)} results but no highlighting"
                        )
                else:
                    print(f"    ❌ FAIL: Expected results for '{query}', found none")

        except Exception as e:
            print(f"    ❌ FAIL: Exception occurred: {e}")

    print(f"📊 Complete search results: {passed}/{total} tests passed")
    return passed == total


async def run_all_mermaid_and_search_tests():
    """Run all Mermaid and search tests."""
    print("🚀 Running Mermaid and Search Fix Tests...")
    print("=" * 60)

    # Test 1: Mermaid syntax validation
    test1_result = test_mermaid_syntax_validation()

    # Test 2: Search result highlighting
    test2_result = test_search_result_highlighting()

    # Test 3: Complete search with highlighting
    test3_result = test_search_with_highlighting()

    # Summary
    print("=" * 60)
    print("📊 Mermaid and Search Fix Test Summary")
    print("-" * 40)
    print(f"Mermaid Syntax Validation: {'✅ PASS' if test1_result else '❌ FAIL'}")
    print(f"Search Result Highlighting: {'✅ PASS' if test2_result else '❌ FAIL'}")
    print(f"Complete Search Functionality: {'✅ PASS' if test3_result else '❌ FAIL'}")

    overall_result = test1_result and test2_result and test3_result
    print(
        f"\nOverall Result: {'✅ ALL TESTS PASSED' if overall_result else '❌ SOME TESTS FAILED'}"
    )

    if overall_result:
        print("\n🎉 All Mermaid and search fix tests passed!")
        print("✅ Mermaid syntax validation is working correctly")
        print("✅ Search result highlighting is working correctly")
        print("✅ Complete search functionality is working correctly")
    else:
        print("\n⚠️ Some tests failed.")
        print("Please check the failed tests above.")

    return overall_result


if __name__ == "__main__":
    asyncio.run(run_all_mermaid_and_search_tests())
