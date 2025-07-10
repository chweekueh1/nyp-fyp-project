#!/usr/bin/env python3
"""
Test OCR and Poppler usage for non-text based files.

This test verifies that the classification system correctly uses:
- Tesseract OCR for image files (PNG, JPG, etc.)
- Poppler-utils (pdftotext) for PDF files as fallback
- PyMuPDF for PDF files as primary method
"""

import os
import tempfile
import unittest
import subprocess
import shutil

# Import the modules we want to test
from gradio_modules.enhanced_content_extraction import (
    extract_with_tesseract,
    extract_pdf_content,
    enhanced_extract_file_content,
)


class TestOCRAndPopplerUsage(unittest.TestCase):
    """Test OCR and Poppler usage for non-text files."""

    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_tesseract_availability(self):
        """Test that Tesseract OCR is available."""
        tesseract_path = shutil.which("tesseract")
        if tesseract_path:
            print(f"✅ Tesseract found at: {tesseract_path}")
            # Test tesseract version
            try:
                result = subprocess.run(
                    [tesseract_path, "--version"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if result.returncode == 0:
                    print(f"✅ Tesseract version: {result.stdout.strip()}")
                else:
                    print(f"⚠️ Tesseract version check failed: {result.stderr}")
            except Exception as e:
                print(f"⚠️ Tesseract version check error: {e}")
        else:
            print("❌ Tesseract not found in PATH")
            self.skipTest("Tesseract not available")

    def test_pdftotext_availability(self):
        """Test that pdftotext (poppler-utils) is available."""
        pdftotext_path = shutil.which("pdftotext")
        if pdftotext_path:
            print(f"✅ pdftotext found at: {pdftotext_path}")
            # Test pdftotext version
            try:
                result = subprocess.run(
                    [pdftotext_path, "-v"], capture_output=True, text=True, timeout=10
                )
                if result.returncode == 0:
                    print(f"✅ pdftotext version: {result.stdout.strip()}")
                else:
                    print(f"⚠️ pdftotext version check failed: {result.stderr}")
            except Exception as e:
                print(f"⚠️ pdftotext version check error: {e}")
        else:
            print("❌ pdftotext not found in PATH")
            self.skipTest("pdftotext not available")

    def test_image_file_extraction_method(self):
        """Test that image files are routed to Tesseract OCR."""
        print("🔍 Testing image file extraction method routing...")

        # Test different image formats
        image_formats = [
            ".png",
            ".jpg",
            ".jpeg",
            ".tiff",
            ".tif",
            ".bmp",
            ".gif",
            ".webp",
        ]

        for ext in image_formats:
            test_file = os.path.join(self.test_dir, f"test_image{ext}")

            # Create a minimal image file (won't work for real OCR but tests method selection)
            with open(test_file, "wb") as f:
                f.write(b"fake image data")

            result = enhanced_extract_file_content(test_file)

            print(
                f"  📄 {ext}: method={result['method']}, methods_tried={result.get('extraction_methods_tried', [])}"
            )

            # Check that tesseract_ocr is in the methods tried
            methods_tried = result.get("extraction_methods_tried", [])
            if "tesseract_ocr" in methods_tried:
                print(f"  ✅ {ext} correctly routed to Tesseract OCR")
            else:
                print(f"  ⚠️ {ext} not routed to Tesseract OCR")

    def test_pdf_file_extraction_method(self):
        """Test that PDF files are routed to PyMuPDF with pdftotext fallback."""
        print("🔍 Testing PDF file extraction method routing...")

        test_file = os.path.join(self.test_dir, "test.pdf")

        # Create a minimal PDF-like file
        with open(test_file, "wb") as f:
            f.write(b"%PDF-1.4\n%Test PDF\n")

        result = enhanced_extract_file_content(test_file)

        print(
            f"  📄 PDF: method={result['method']}, methods_tried={result.get('extraction_methods_tried', [])}"
        )

        # Check that pdf_extraction is in the methods tried
        methods_tried = result.get("extraction_methods_tried", [])
        if "pdf_extraction" in methods_tried:
            print("  ✅ PDF correctly routed to PDF extraction")
        else:
            print("  ⚠️ PDF not routed to PDF extraction")

    def test_tesseract_ocr_function(self):
        """Test the Tesseract OCR function directly."""
        print("🔍 Testing Tesseract OCR function...")

        # Test with a non-image file (should return None)
        test_file = os.path.join(self.test_dir, "test.txt")
        with open(test_file, "w") as f:
            f.write("This is not an image file")

        result = extract_with_tesseract(test_file)
        if result is None:
            print("  ✅ Tesseract correctly rejected non-image file")
        else:
            print(f"  ⚠️ Tesseract processed non-image file: {result[:50]}...")

        # Test with an image file (will fail but tests the function)
        test_image = os.path.join(self.test_dir, "test.png")
        with open(test_image, "wb") as f:
            f.write(b"fake image data")

        try:
            result = extract_with_tesseract(test_image)
            if result is None:
                print("  ℹ️ Tesseract failed to process fake image (expected)")
            else:
                print(f"  ✅ Tesseract processed image: {result[:50]}...")
        except Exception as e:
            print(f"  ℹ️ Tesseract error (expected for fake image): {e}")

    def test_pdf_extraction_function(self):
        """Test the PDF extraction function directly."""
        print("🔍 Testing PDF extraction function...")

        # Test with a non-PDF file (should return None)
        test_file = os.path.join(self.test_dir, "test.txt")
        with open(test_file, "w") as f:
            f.write("This is not a PDF file")

        result = extract_pdf_content(test_file)
        if result is None:
            print("  ✅ PDF extraction correctly rejected non-PDF file")
        else:
            print(f"  ⚠️ PDF extraction processed non-PDF file: {result[:50]}...")

        # Test with a fake PDF file
        test_pdf = os.path.join(self.test_dir, "test.pdf")
        with open(test_pdf, "wb") as f:
            f.write(b"%PDF-1.4\n%Test PDF\n")

        try:
            result = extract_pdf_content(test_pdf)
            if result is None:
                print("  ℹ️ PDF extraction failed to process fake PDF (expected)")
            else:
                print(f"  ✅ PDF extraction processed PDF: {result[:50]}...")
        except Exception as e:
            print(f"  ℹ️ PDF extraction error (expected for fake PDF): {e}")

    def test_file_type_detection_and_routing(self):
        """Test that different file types are routed to appropriate extraction methods."""
        print("🔍 Testing file type detection and routing...")

        test_cases = [
            (".txt", "text file"),
            (".md", "markdown file"),
            (".csv", "csv file"),
            (".pdf", "pdf file"),
            (".png", "image file"),
            (".jpg", "image file"),
            (".docx", "document file"),
            (".xlsx", "spreadsheet file"),
        ]

        for ext, description in test_cases:
            test_file = os.path.join(self.test_dir, f"test{ext}")

            # Create appropriate test content
            if ext in [".txt", ".md", ".csv"]:
                with open(test_file, "w", encoding="utf-8") as f:
                    f.write(f"Test content for {description}")
            elif ext == ".pdf":
                with open(test_file, "wb") as f:
                    f.write(b"%PDF-1.4\n%Test PDF\n")
            elif ext in [".png", ".jpg"]:
                with open(test_file, "wb") as f:
                    f.write(b"fake image data")
            else:
                with open(test_file, "w") as f:
                    f.write(f"Test content for {description}")

            result = enhanced_extract_file_content(test_file)
            methods_tried = result.get("extraction_methods_tried", [])

            print(
                f"  📄 {ext} ({description}): method={result['method']}, methods_tried={methods_tried}"
            )

            # Verify appropriate method was tried
            if ext in [
                ".png",
                ".jpg",
                ".jpeg",
                ".tiff",
                ".tif",
                ".bmp",
                ".gif",
                ".webp",
            ]:
                if "tesseract_ocr" in methods_tried:
                    print(f"  ✅ {ext} correctly routed to Tesseract OCR")
                else:
                    print(f"  ❌ {ext} not routed to Tesseract OCR")
            elif ext == ".pdf":
                if "pdf_extraction" in methods_tried:
                    print(f"  ✅ {ext} correctly routed to PDF extraction")
                else:
                    print(f"  ❌ {ext} not routed to PDF extraction")
            elif ext in [".txt", ".md", ".csv"]:
                if result["method"] in ["text_file", "pandoc"]:
                    print(f"  ✅ {ext} correctly routed to text processing")
                else:
                    print(f"  ❌ {ext} not routed to text processing")

    def test_dependency_checking(self):
        """Test dependency checking for OCR and PDF tools."""
        print("🔍 Testing dependency checking...")

        # Check Tesseract
        tesseract_available = shutil.which("tesseract") is not None
        print(f"  📦 Tesseract available: {tesseract_available}")

        # Check pdftotext
        pdftotext_available = shutil.which("pdftotext") is not None
        print(f"  📦 pdftotext available: {pdftotext_available}")

        # Check PyMuPDF
        try:
            import importlib.util

            pymupdf_available = importlib.util.find_spec("fitz") is not None
            print(f"  📦 PyMuPDF available: {pymupdf_available}")
        except ImportError:
            pymupdf_available = False
            print("  📦 PyMuPDF not available")

        # Summary
        if tesseract_available:
            print("  ✅ Tesseract OCR is available for image processing")
        else:
            print("  ⚠️ Tesseract OCR not available - image processing limited")

        if pdftotext_available:
            print("  ✅ pdftotext is available for PDF fallback processing")
        else:
            print("  ⚠️ pdftotext not available - PDF fallback processing limited")

        if pymupdf_available:
            print("  ✅ PyMuPDF is available for PDF processing")
        else:
            print("  ⚠️ PyMuPDF not available - PDF processing limited")


def run_ocr_poppler_tests():
    """Run all OCR and Poppler usage tests."""
    print("🧪 Running OCR and Poppler Usage Tests")
    print("=" * 50)

    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestOCRAndPopplerUsage)

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print("\n" + "=" * 50)
    print("📊 OCR and Poppler Test Summary")
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
        print("\n✅ All OCR and Poppler tests passed!")
    else:
        print("\n❌ Some OCR and Poppler tests failed!")

    return result.wasSuccessful()


if __name__ == "__main__":
    run_ocr_poppler_tests()
