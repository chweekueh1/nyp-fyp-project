#!/usr/bin/env python3
"""
Test script to verify special character handling in enhanced_content_extraction.
Tests that only text-based files have special characters cleaned before pandoc parsing.
"""

import sys
import os
import tempfile
from pathlib import Path

# Add parent directory to path for imports
parent_dir = Path(__file__).parent.parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from gradio_modules.enhanced_content_extraction import (
    escape_special_characters,
    apply_text_processing,
    extract_with_pandoc,
    enhanced_extract_file_content,
)


def test_escape_special_characters():
    """Test the escape_special_characters function with refined regex pattern."""
    print("🔍 Testing escape_special_characters function...")
    try:
        # Test cases updated for the refined regex pattern
        test_cases = [
            (
                "Hello, world! How are you?",
                "Hello, world! How are you?",
            ),  # Preserves punctuation
            (
                "File@name#with$special%chars",
                "File@name#with$special%chars",
            ),  # Preserves symbols
            ("Normal text with spaces", "Normal text with spaces"),  # No change
            ("Text\nwith\nnewlines", "Text\nwith\nnewlines"),  # Newlines preserved
            ("Text\twith\ttabs", "Text\twith\ttabs"),  # Tabs preserved (part of \s)
            ("Unicode: éñçüß", "Unicode: éñçüß"),  # Unicode preserved
            (
                "HTML: <tag>content</tag>",
                "HTML: <tag>content</tag>",
            ),  # HTML tags preserved
            (
                "Markdown: **bold** *italic*",
                "Markdown: **bold** *italic*",
            ),  # Markdown preserved
            ("Code: `print('hello')`", "Code: `print('hello')`"),  # Code preserved
            (
                "Math: 2+2=4, x²+y²=z²",
                "Math: 2+2=4, x²+y²=z²",
            ),  # Math symbols preserved
            ("Email: user@domain.com", "Email: user@domain.com"),  # Email preserved
            ("URL: https://example.com", "URL: https://example.com"),  # URL preserved
            # Test problematic characters that should be removed
            (
                "Text with \x00\x01\x02 control chars",
                "Text with   control chars",
            ),  # Control chars removed
            (
                "Text with \x7f\x80\x81 extended chars",
                "Text with   extended chars",
            ),  # Extended chars removed
        ]

        for input_text, expected in test_cases:
            result = escape_special_characters(input_text)
            assert result == expected, (
                f"Input: {repr(input_text)}\n"
                f"Expected: {repr(expected)}\n"
                f"Result: {repr(result)}"
            )
            print(f"  ✅ Test case passed: {repr(input_text[:30])}...")

        print("✅ test_escape_special_characters: PASSED")
    except Exception as e:
        print(f"❌ test_escape_special_characters: FAILED - {e}")
        import traceback

        traceback.print_exc()
        raise


def test_text_based_file_extraction():
    """Test that only text-based files have special characters cleaned before pandoc."""
    print("🔍 Testing text-based file extraction with special characters...")

    # Create test files
    test_files = {}

    # Test .txt file with special characters
    txt_content = """Hello, world! This is a test file.
It contains special characters like: @#$%^&*()_+-=[]{}|;':",./<>?
Also some HTML-like content: <tag>content</tag>
And markdown: **bold** *italic* `code`
Unicode characters: éñçüß
Email: test@example.com
URL: https://example.com
Math: 2+2=4, x²+y²=z²
"""

    # Test .md file with special characters
    md_content = """# Test Markdown File

This is a **bold** and *italic* text.

## Special Characters
- @#$%^&*()_+-=[]{}|;':",./<>?
- HTML: <div>content</div>
- Code: `print('hello')`
- Unicode: éñçüß
- Email: test@example.com
- URL: https://example.com
"""

    # Create temporary files
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False, encoding="utf-8"
    ) as f:
        f.write(txt_content)
        test_files["txt"] = f.name

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".md", delete=False, encoding="utf-8"
    ) as f:
        f.write(md_content)
        test_files["md"] = f.name

    try:
        for file_type, file_path in test_files.items():
            print(f"\n--- Testing {file_type.upper()} file ---")

            # Read original content
            with open(file_path, "r", encoding="utf-8") as f:
                original_content = f.read()
            print(f"  Original content length: {len(original_content)}")

            # Test enhanced extraction
            result = enhanced_extract_file_content(file_path)
            print(f"  Extraction method: {result['method']}")
            print(f"  Extraction error: {result['error']}")
            print(f"  Extracted content length: {len(result['content'])}")

            # Verify that text-based files are processed correctly
            assert result["content"], f"No content extracted from {file_type} file"
            assert result["method"] in ["pandoc", "text_file"], (
                f"Expected pandoc or text_file method for {file_type}, got {result['method']}"
            )
            print(f"  ✅ {file_type} file processed successfully")

            # Test direct pandoc extraction
            pandoc_result = extract_with_pandoc(file_path)
            if pandoc_result:
                print(f"  Pandoc extraction successful, length: {len(pandoc_result)}")
                # Verify that special characters are preserved (not overly cleaned)
                assert any(
                    char in pandoc_result for char in "@#$%^&*()_+-=[]{}|;':\",./<>?"
                ), (
                    f"Expected special characters to be preserved in pandoc result for {file_type}"
                )
                print("  ✅ Special characters preserved in pandoc result")
            else:
                print(f"  ⚠️ Pandoc extraction failed for {file_type}")

            print("-" * 50)

    finally:
        # Clean up test files
        for file_path in test_files.values():
            try:
                os.unlink(file_path)
            except Exception as e:
                print(f"Warning: Could not delete {file_path}: {e}")

    print("✅ test_text_based_file_extraction: PASSED")


def test_text_processing_function():
    """Test the apply_text_processing function for keyword filtering and special character cleaning."""
    print("🔍 Testing apply_text_processing function...")
    try:
        # Test text-based files should be processed
        text_content = "The quick brown fox jumps over the lazy dog. This is a test with special chars: @#$%^&*()"

        # Test .txt file processing
        result_txt = apply_text_processing(text_content, ".txt")
        assert result_txt != text_content, "Text file should be processed"
        print("  ✅ .txt file processing applied")

        # Test .md file processing
        result_md = apply_text_processing(text_content, ".md")
        assert result_md != text_content, "Markdown file should be processed"
        print("  ✅ .md file processing applied")

        # Test .csv file processing
        result_csv = apply_text_processing(text_content, ".csv")
        assert result_csv != text_content, "CSV file should be processed"
        print("  ✅ .csv file processing applied")

        # Test .log file processing
        result_log = apply_text_processing(text_content, ".log")
        assert result_log != text_content, "Log file should be processed"
        print("  ✅ .log file processing applied")

        # Test non-text-based files should NOT be processed
        result_pdf = apply_text_processing(text_content, ".pdf")
        assert result_pdf == text_content, "PDF file should NOT be processed"
        print("  ✅ .pdf file processing skipped")

        result_docx = apply_text_processing(text_content, ".docx")
        assert result_docx == text_content, "DOCX file should NOT be processed"
        print("  ✅ .docx file processing skipped")

        result_png = apply_text_processing(text_content, ".png")
        assert result_png == text_content, "PNG file should NOT be processed"
        print("  ✅ .png file processing skipped")

        # Test that filler words are removed (keyword filtering)
        filler_text = "The and or but in on at to for of with by from up down the a an"
        processed_filler = apply_text_processing(filler_text, ".txt")
        # Should remove common filler words like "the", "and", "or", "but", etc.
        assert len(processed_filler.split()) < len(filler_text.split()), (
            "Filler words should be removed"
        )
        print("  ✅ Filler word removal verified")

        print("✅ test_text_processing_function: PASSED")
    except Exception as e:
        print(f"❌ test_text_processing_function: FAILED - {e}")
        import traceback

        traceback.print_exc()
        raise


def test_pdf_files_not_cleaned():
    """Test that PDF files are NOT processed with special character cleaning."""
    print("🔍 Testing that PDF files are not cleaned with special characters...")

    # Create a mock PDF content (simulating what might come from a PDF)
    pdf_content = """PDF Content Test

This simulates content that might come from a PDF.
Special characters: @#$%^&*()_+-=[]{}|;':",./<>?
Unicode: éñçüß
HTML entities: &lt; &gt; &amp;
Math symbols: 2+2=4, x²+y²=z²
"""

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".pdf", delete=False, encoding="utf-8"
    ) as f:
        f.write(pdf_content)
        test_file = f.name

    try:
        print(f"Test PDF file: {test_file}")

        # Test enhanced extraction
        result = enhanced_extract_file_content(test_file)
        print(f"Extraction method: {result['method']}")
        print(f"Extraction error: {result['error']}")

        # PDF files should be processed by pdf_extraction method, not pandoc with cleaning
        if result["method"] == "pdf_extraction":
            print("✅ PDF file correctly processed by pdf_extraction method")
        elif result["method"] == "pandoc":
            # If pandoc is used, verify that special characters are NOT cleaned
            # (since PDF was removed from the cleaning list)
            if result["content"]:
                assert any(
                    char in result["content"]
                    for char in "@#$%^&*()_+-=[]{}|;':\",./<>?"
                ), "Expected special characters to be preserved in PDF pandoc result"
                print(
                    "✅ PDF file processed by pandoc without special character cleaning"
                )
        else:
            print(f"⚠️ PDF file processed by unexpected method: {result['method']}")

    finally:
        try:
            os.unlink(test_file)
        except Exception as e:
            print(f"Warning: Could not delete {test_file}: {e}")

    print("✅ test_pdf_files_not_cleaned: PASSED")


def run_special_character_tests():
    """Run all special character handling tests."""
    print("🚀 Running Special Character Handling Tests...")
    print("=" * 60)

    test_functions = [
        test_escape_special_characters,
        test_text_based_file_extraction,
        test_text_processing_function,
        test_pdf_files_not_cleaned,
    ]

    passed = 0
    total = len(test_functions)

    for test_func in test_functions:
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"❌ {test_func.__name__}: FAILED - {e}")
            import traceback

            traceback.print_exc()

    print(f"\n{'=' * 60}")
    print("SPECIAL CHARACTER TESTS SUMMARY")
    print("=" * 60)
    print(f"Passed: {passed}/{total}")

    if passed == total:
        print("✅ All special character tests passed!")
        return True
    else:
        print(f"❌ {total - passed} test(s) failed")
        return False


if __name__ == "__main__":
    success = run_special_character_tests()
    sys.exit(0 if success else 1)
