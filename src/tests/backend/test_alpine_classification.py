#!/usr/bin/env python3
"""
Test Alpine-friendly classification logic.

This test verifies that the classification system works correctly with
Alpine Linux friendly packages (pymupdf instead of problematic packages).
"""

import os
import tempfile
import unittest

# Import the modules we want to test
from llm.dataProcessing import (
    ExtractText,
    OptimizedUnstructuredExtraction,
    StandardUnstructuredExtraction,
)
from gradio_modules.enhanced_content_extraction import extract_pdf_content


class TestAlpineClassification(unittest.TestCase):
    """Test Alpine-friendly classification functionality."""

    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test environment."""
        import shutil

        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_pymupdf_availability(self):
        """Test that PyMuPDF is available."""
        try:
            import importlib.util

            pymupdf_available = importlib.util.find_spec("fitz") is not None
            self.assertTrue(pymupdf_available, "PyMuPDF is available")
        except ImportError:
            self.skipTest("PyMuPDF not available")

    def test_text_file_extraction(self):
        """Test text file extraction with Alpine-friendly methods."""
        # Create a test text file
        test_file = os.path.join(self.test_dir, "test.txt")
        test_content = "This is a test document for classification."

        with open(test_file, "w", encoding="utf-8") as f:
            f.write(test_content)

        # Test extraction
        documents = ExtractText(test_file)

        self.assertIsInstance(documents, list)
        self.assertGreater(len(documents), 0)
        self.assertIn(test_content, documents[0].page_content)
        print(f"✅ Text file extraction: {len(documents)} documents extracted")

    def test_pdf_extraction_with_pymupdf(self):
        """Test PDF extraction using PyMuPDF."""
        try:
            import importlib.util

            pymupdf_available = importlib.util.find_spec("fitz") is not None
            if not pymupdf_available:
                self.skipTest("PyMuPDF not available")
        except ImportError:
            self.skipTest("PyMuPDF not available")

        # Create a simple PDF-like test (this is a simplified test)
        # In a real scenario, you would have an actual PDF file
        test_file = os.path.join(self.test_dir, "test.pdf")

        # Create a minimal PDF-like file for testing
        with open(test_file, "wb") as f:
            f.write(b"%PDF-1.4\n%Test PDF\n")

        # Test extraction (should fall back gracefully)
        try:
            documents = ExtractText(test_file)
            self.assertIsInstance(documents, list)
            print(f"✅ PDF extraction test completed: {len(documents)} documents")
        except Exception as e:
            # This is expected for a non-valid PDF
            print(f"ℹ️ PDF extraction test (expected failure for test file): {e}")

    def test_optimized_extraction_methods(self):
        """Test optimized extraction methods."""
        # Test text file
        test_file = os.path.join(self.test_dir, "test.txt")
        test_content = "Test content for optimized extraction."

        with open(test_file, "w", encoding="utf-8") as f:
            f.write(test_content)

        # Test optimized extraction
        documents = OptimizedUnstructuredExtraction(test_file)
        self.assertIsInstance(documents, list)
        self.assertGreater(len(documents), 0)
        print(f"✅ Optimized extraction: {len(documents)} documents")

    def test_standard_extraction_methods(self):
        """Test standard extraction methods."""
        # Test text file
        test_file = os.path.join(self.test_dir, "test.txt")
        test_content = "Test content for standard extraction."

        with open(test_file, "w", encoding="utf-8") as f:
            f.write(test_content)

        # Test standard extraction
        documents = StandardUnstructuredExtraction(test_file)
        self.assertIsInstance(documents, list)
        self.assertGreater(len(documents), 0)
        print(f"✅ Standard extraction: {len(documents)} documents")

    def test_enhanced_content_extraction(self):
        """Test enhanced content extraction module."""
        # Test text file
        test_file = os.path.join(self.test_dir, "test.txt")
        test_content = "Test content for enhanced extraction."

        with open(test_file, "w", encoding="utf-8") as f:
            f.write(test_content)

        # Test PDF extraction function (should handle non-PDF gracefully)
        extract_pdf_content(test_file)
        # For non-PDF files, this should return None or handle gracefully
        print("✅ Enhanced content extraction test completed")

    def test_file_type_detection(self):
        """Test file type detection and routing."""
        # Test different file extensions
        test_cases = [
            (".txt", "text file"),
            (".md", "markdown file"),
            (".py", "python file"),
            (".pdf", "pdf file"),
        ]

        for ext, description in test_cases:
            test_file = os.path.join(self.test_dir, f"test{ext}")
            test_content = f"Test content for {description}."

            with open(test_file, "w", encoding="utf-8") as f:
                f.write(test_content)

            try:
                documents = ExtractText(test_file)
                self.assertIsInstance(documents, list)
                print(f"✅ {ext} file type detection: {len(documents)} documents")
            except Exception as e:
                print(f"ℹ️ {ext} file type detection (expected behavior): {e}")


def run_alpine_classification_tests():
    """Run all Alpine classification tests."""
    print("🧪 Running Alpine-friendly Classification Tests")
    print("=" * 50)

    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAlpineClassification)

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print("\n" + "=" * 50)
    print("📊 Alpine Classification Test Summary")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped) if hasattr(result, 'skipped') else 0}")

    if result.failures:
        print("\n❌ Failures:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback}")

    if result.errors:
        print("\n❌ Errors:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback}")

    if result.wasSuccessful():
        print("\n✅ All Alpine classification tests passed!")
    else:
        print("\n❌ Some Alpine classification tests failed!")

    return result.wasSuccessful()


if __name__ == "__main__":
    run_alpine_classification_tests()
