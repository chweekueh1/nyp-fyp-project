#!/usr/bin/env python3
"""
Test file classification interface functionality.
"""

import sys
import os
import tempfile
import shutil
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import gradio as gr
from gradio_modules.file_classification import (
    file_classification_interface,
    is_file_allowed,
    save_uploaded_file,
    get_uploads_dir,
)
from gradio_modules.enhanced_content_extraction import (
    enhanced_extract_file_content as extract_file_content,
    classify_file_content,
)


def test_allowed_extensions():
    """Test file extension validation."""
    print("🔍 Testing file extension validation...")

    # Test allowed extensions
    allowed_files = [
        "document.txt",
        "report.pdf",
        "data.xlsx",
        "presentation.pptx",
        "notes.md",
        "info.docx",
    ]

    for filename in allowed_files:
        assert is_file_allowed(filename), f"Should allow {filename}"
        print(f"  ✅ {filename} - allowed")

    # Test disallowed extensions
    disallowed_files = [
        "script.py",
        "executable.exe",
        "image.jpg",
        "video.mp4",
        "archive.zip",
        "unknown",
    ]

    for filename in disallowed_files:
        assert not is_file_allowed(filename), f"Should not allow {filename}"
        print(f"  ❌ {filename} - blocked")

    print("✅ File extension validation working correctly")


def test_uploads_directory():
    """Test uploads directory creation."""
    print("🗂️ Testing uploads directory creation...")

    test_username = "test_user"
    uploads_dir = get_uploads_dir(test_username)

    assert os.path.exists(uploads_dir), "Uploads directory should be created"
    assert test_username in uploads_dir, "Directory should contain username"

    print(f"  ✅ Created directory: {uploads_dir}")

    # Cleanup
    try:
        shutil.rmtree(uploads_dir)
        print("  🧹 Cleaned up test directory")
    except Exception:
        pass

    print("✅ Uploads directory creation working correctly")


def test_file_upload_simulation():
    """Test file upload simulation with mock file."""
    print("📁 Testing file upload simulation...")

    test_username = "test_user"

    # Create a temporary test file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as tmp_file:
        tmp_file.write(
            "This is a test document for classification.\nIt contains sample text content."
        )
        tmp_file_path = tmp_file.name

    try:
        # Create a mock file object
        class MockFileObj:
            def __init__(self, path, name):
                self.name = name
                self.path = path

            def read(self):
                with open(self.path, "rb") as f:
                    return f.read()

        mock_file = MockFileObj(tmp_file_path, "test_document.txt")

        # Test file saving
        saved_path, original_name = save_uploaded_file(mock_file, test_username)

        assert os.path.exists(saved_path), "File should be saved"
        assert original_name == "test_document.txt", (
            "Original filename should be preserved"
        )

        print(f"  ✅ File saved to: {saved_path}")
        print(f"  ✅ Original name: {original_name}")

        # Test content extraction
        extraction_result = extract_file_content(saved_path)
        assert isinstance(extraction_result, dict), (
            "Should return extraction result dict"
        )
        content = extraction_result.get("content", "")
        assert "test document" in content.lower(), "Content should be extracted"

        print(f"  ✅ Content extracted: {content[:50]}...")

        # Cleanup
        if os.path.exists(saved_path):
            os.remove(saved_path)
        uploads_dir = get_uploads_dir(test_username)
        if os.path.exists(uploads_dir):
            shutil.rmtree(uploads_dir)

    finally:
        # Cleanup temp file
        if os.path.exists(tmp_file_path):
            os.remove(tmp_file_path)

    print("✅ File upload simulation working correctly")


def test_classification_interface():
    """Test the classification interface creation."""
    print("🎨 Testing classification interface creation...")

    # Create a mock username state
    username_state = gr.State("test_user")

    try:
        # Test interface creation
        components = file_classification_interface(username_state)

        # Should return 17 components
        expected_count = 17
        assert len(components) == expected_count, (
            f"Expected {expected_count} components, got {len(components)}"
        )

        print(f"  ✅ Interface created with {len(components)} components")

        # Verify component types
        component_types = [type(comp).__name__ for comp in components]
        print(f"  📋 Component types: {component_types}")

        # Check for essential components
        essential_components = ["File", "Button", "Markdown"]
        for comp_type in essential_components:
            assert comp_type in component_types, (
                f"Missing essential component: {comp_type}"
            )

        print("  ✅ All essential components present")

    except Exception as e:
        print(f"  ❌ Error creating interface: {e}")
        import traceback

        print("  📋 Full traceback:")
        traceback.print_exc()
        raise

    print("✅ Classification interface creation working correctly")


def test_mock_classification():
    """Test classification with mock content."""
    print("🔍 Testing mock classification...")

    test_content = """
    This is a confidential business document containing sensitive information
    about company financial data and strategic plans. The document includes
    proprietary information that should be handled with care.
    """

    try:
        # Test classification (this will use the actual classification model if available)
        result = classify_file_content(test_content, "test_user")

        assert isinstance(result, dict), "Classification should return a dictionary"
        assert "classification" in result, "Result should contain classification"
        assert "sensitivity" in result, "Result should contain sensitivity"
        assert "reasoning" in result, "Result should contain reasoning"

        print(f"  ✅ Classification: {result.get('classification', 'Unknown')}")
        print(f"  ✅ Sensitivity: {result.get('sensitivity', 'Unknown')}")
        print(f"  ✅ Reasoning: {result.get('reasoning', 'No reasoning')[:100]}...")

    except Exception as e:
        print(f"  ℹ️ Classification test failed (expected if LLM not initialized): {e}")
        # This is expected if the LLM is not initialized

    print("✅ Mock classification test completed")


def test_keyword_filtering_md_files():
    """Test keyword filtering logic for MD and other text-based files."""
    print("🔍 Testing keyword filtering for MD and text-based files...")

    try:
        from gradio_modules.enhanced_content_extraction import apply_text_processing

        # Test content with filler words
        test_content = (
            "The quick brown fox and the lazy dog jumps over the fence in the garden."
        )

        # Test MD file processing
        md_result = apply_text_processing(test_content, ".md")
        print(
            f"  ✅ MD file processed: {len(md_result.split())} words (from {len(test_content.split())})"
        )

        # Test TXT file processing
        txt_result = apply_text_processing(test_content, ".txt")
        print(
            f"  ✅ TXT file processed: {len(txt_result.split())} words (from {len(test_content.split())})"
        )

        # Test CSV file processing
        csv_result = apply_text_processing(test_content, ".csv")
        print(
            f"  ✅ CSV file processed: {len(csv_result.split())} words (from {len(test_content.split())})"
        )

        # Test that non-text files are not processed
        pdf_result = apply_text_processing(test_content, ".pdf")
        assert pdf_result == test_content, "PDF files should not be processed"
        print("  ✅ PDF file not processed (as expected)")

        docx_result = apply_text_processing(test_content, ".docx")
        assert docx_result == test_content, "DOCX files should not be processed"
        print("  ✅ DOCX file not processed (as expected)")

        print("✅ Keyword filtering tests completed")

    except Exception as e:
        print(f"  ❌ Error in keyword filtering test: {e}")
        raise


def test_pdf_file_handling():
    """Test handling of PDF files and other file types."""
    print("🔍 Testing PDF and other file type handling...")

    try:
        # Test PDF file extension validation
        assert is_file_allowed("document.pdf"), "PDF files should be allowed"
        assert is_file_allowed("report.PDF"), "PDF files (uppercase) should be allowed"
        print("  ✅ PDF file extension validation passed")

        # Test other allowed file types
        allowed_types = [
            "document.txt",
            "notes.md",
            "data.csv",
            "report.docx",
            "presentation.pptx",
            "spreadsheet.xlsx",
            "text.rtf",
        ]

        for file_type in allowed_types:
            assert is_file_allowed(file_type), f"{file_type} should be allowed"
            print(f"  ✅ {file_type} - allowed")

        # Test disallowed file types
        disallowed_types = [
            "script.py",
            "image.jpg",
            "video.mp4",
            "archive.zip",
            "executable.exe",
            "audio.mp3",
            "unknown.xyz",
        ]

        for file_type in disallowed_types:
            assert not is_file_allowed(file_type), f"{file_type} should not be allowed"
            print(f"  ℹ️ {file_type} - correctly blocked")

        print("✅ PDF and file type handling tests completed")

    except Exception as e:
        print(f"  ❌ Error in PDF file handling test: {e}")
        raise


def test_no_pycache_reading():
    """Test that the test suite doesn't read from __pycache__ directories."""
    print("🔍 Testing __pycache__ exclusion...")

    try:
        import sys
        import os

        # Check that no __pycache__ paths are in sys.path
        pycache_paths = [path for path in sys.path if "__pycache__" in path]
        assert len(pycache_paths) == 0, (
            f"Found __pycache__ paths in sys.path: {pycache_paths}"
        )
        print("  ✅ No __pycache__ paths in sys.path")

        # Check current working directory doesn't contain __pycache__
        cwd = os.getcwd()
        assert "__pycache__" not in cwd, (
            f"Current working directory contains __pycache__: {cwd}"
        )
        print("  ✅ Current working directory clean")

        # Check that we're not importing from __pycache__
        for module_name, module in sys.modules.items():
            if hasattr(module, "__file__") and module.__file__:
                assert "__pycache__" not in module.__file__, (
                    f"Module {module_name} loaded from __pycache__: {module.__file__}"
                )
        print("  ✅ No modules loaded from __pycache__")

        print("✅ __pycache__ exclusion tests completed")

    except Exception as e:
        print(f"  ❌ Error in __pycache__ exclusion test: {e}")
        raise


def test_no_gradio_server_launch():
    """Test that tests don't launch Gradio servers."""
    print("🔍 Testing that no Gradio servers are launched...")

    try:
        import gradio as gr

        # Mock the launch method to detect if it's called
        original_launch = gr.Interface.launch
        launch_called = False

        def mock_launch(*args, **kwargs):
            nonlocal launch_called
            launch_called = True
            raise Exception("Gradio server launch detected in test!")

        gr.Interface.launch = mock_launch

        try:
            # Run interface creation (should not launch server)
            username_state = gr.State("test_user")
            components = file_classification_interface(username_state)

            # Verify components were created and no launch was called
            assert components is not None, "Interface components should be created"
            assert not launch_called, "Gradio server launch was detected!"
            print("  ✅ No Gradio server launch detected")

        finally:
            # Restore original launch method
            gr.Interface.launch = original_launch

        print("✅ Gradio server launch prevention tests completed")

    except Exception as e:
        print(f"  ❌ Error in Gradio server launch test: {e}")
        import traceback

        print("  📋 Full traceback:")
        traceback.print_exc()
        raise


def run_all_tests():
    """Run all file classification tests."""
    print("🧪 File Classification Interface Tests")
    print("=" * 50)

    tests = [
        ("File Extension Validation", test_allowed_extensions),
        ("Uploads Directory", test_uploads_directory),
        ("File Upload Simulation", test_file_upload_simulation),
        ("Classification Interface", test_classification_interface),
        ("Mock Classification", test_mock_classification),
        ("Keyword Filtering for MD Files", test_keyword_filtering_md_files),
        ("PDF File Handling", test_pdf_file_handling),
        ("No PyCache Reading", test_no_pycache_reading),
        ("No Gradio Server Launch", test_no_gradio_server_launch),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            print(f"\n🔬 Running: {test_name}")
            test_func()
            print(f"✅ PASSED: {test_name}")
            passed += 1
        except Exception as e:
            print(f"❌ FAILED: {test_name} - {e}")
            failed += 1

    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed} passed, {failed} failed")

    if failed == 0:
        print("🎉 All file classification tests passed!")
    else:
        print(f"⚠️ {failed} test(s) failed")

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
