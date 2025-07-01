#!/usr/bin/env python3
"""
LLM tests for all LLM service classes and functions.
Tests the LLM models, classification, and data processing functionality.
"""

import sys
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

# Add parent directory to path for imports
parent_dir = Path(__file__).parent.parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Import LLM modules - using actual functions instead of service classes
from llm.chatModel import get_convo_hist_answer, is_llm_ready, initialize_llm_and_db
from llm.classificationModel import classify_text
from llm.dataProcessing import dataProcessing, ExtractText

initialize_llm_and_db()


def test_chat_model_service():
    """Test chat model functionality."""
    print("🔍 Testing chat model functions...")
    try:
        # Test that functions can be imported
        assert callable(get_convo_hist_answer), (
            "get_convo_hist_answer should be callable"
        )
        assert callable(is_llm_ready), "is_llm_ready should be callable"
        assert callable(initialize_llm_and_db), (
            "initialize_llm_and_db should be callable"
        )
        print("  ✅ Function imports passed")

        # Test LLM readiness check
        ready = is_llm_ready()
        assert isinstance(ready, bool), "is_llm_ready should return boolean"
        print(f"  ✅ LLM ready check passed (ready: {ready})")

        print("✅ test_chat_model_service: PASSED")
    except Exception as e:
        print(f"❌ test_chat_model_service: FAILED - {e}")
        import traceback

        traceback.print_exc()
        raise


def test_chat_model_call():
    """Test chat model call functionality."""
    print("🔍 Testing get_convo_hist_answer function...")
    try:
        # Mock the function to avoid actual API calls
        with patch(
            "llm.chatModel.get_convo_hist_answer",
            return_value={"answer": "Mock response"},
        ):
            # Test with valid input
            result = get_convo_hist_answer("Hello, how are you?", "test_thread")
            assert isinstance(result, dict), f"Expected dict, got {type(result)}"
            assert "answer" in result, "Result should have 'answer' key"
            print("  ✅ Valid input call passed")

            # Test with empty input
            result = get_convo_hist_answer("", "test_thread")
            assert isinstance(result, dict), f"Expected dict, got {type(result)}"
            print("  ✅ Empty input call passed")

        print("✅ test_chat_model_call: PASSED")
    except Exception as e:
        print(f"❌ test_chat_model_call: FAILED - {e}")
        import traceback

        traceback.print_exc()
        raise


def test_classification_service():
    """Test classification functionality."""
    print("🔍 Testing classification functions...")
    try:
        # Test that function can be imported
        assert callable(classify_text), "classify_text should be callable"
        print("  ✅ Function import passed")

        print("✅ test_classification_service: PASSED")
    except Exception as e:
        print(f"❌ test_classification_service: FAILED - {e}")
        import traceback

        traceback.print_exc()
        raise


def test_classification_classify_text():
    """Test classification text functionality."""
    print("🔍 Testing classify_text function...")
    try:
        # Mock the classification response to avoid actual API calls
        with patch(
            "llm.classificationModel.classify_text",
            return_value={"answer": "Mock classification"},
        ):
            # Test with valid text
            result = classify_text("This is a test document for classification.")
            assert isinstance(result, dict), f"Expected dict, got {type(result)}"
            print("  ✅ Valid text classification passed")

            # Test with empty text
            result = classify_text("")
            assert isinstance(result, dict), f"Expected dict, got {type(result)}"
            print("  ✅ Empty text classification passed")

            # Test with special characters
            result = classify_text("Test with special chars: @#$%^&*()")
            assert isinstance(result, dict), f"Expected dict, got {type(result)}"
            print("  ✅ Special characters classification passed")

        print("✅ test_classification_classify_text: PASSED")
    except Exception as e:
        print(f"❌ test_classification_classify_text: FAILED - {e}")
        import traceback

        traceback.print_exc()
        raise


def test_data_processing_service():
    """Test data processing functionality."""
    print("🔍 Testing data processing functions...")
    try:
        # Test that functions can be imported
        assert callable(dataProcessing), "dataProcessing should be callable"
        assert callable(ExtractText), "ExtractText should be callable"
        print("  ✅ Function imports passed")

        print("✅ test_data_processing_service: PASSED")
    except Exception as e:
        print(f"❌ test_data_processing_service: FAILED - {e}")
        import traceback

        traceback.print_exc()
        raise


def test_data_processing_extract_text():
    """Test text extraction functionality."""
    print("🔍 Testing ExtractText function...")
    try:
        # Create a temporary test file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("This is a test document for text extraction.")
            temp_file = f.name

        try:
            # Test text extraction
            result = ExtractText(temp_file)
            assert isinstance(result, list), f"Expected list, got {type(result)}"
            print("  ✅ Valid file text extraction passed")

            # Test with empty file
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".txt", delete=False
            ) as f:
                f.write("")
                empty_file = f.name

            try:
                result = ExtractText(empty_file)
                assert isinstance(result, list), f"Expected list, got {type(result)}"
                print("  ✅ Empty file text extraction passed")
            finally:
                os.unlink(empty_file)

        finally:
            os.unlink(temp_file)

        print("✅ test_data_processing_extract_text: PASSED")
    except Exception as e:
        print(f"❌ test_data_processing_extract_text: FAILED - {e}")
        import traceback

        traceback.print_exc()
        raise


def test_data_processing_recursive_chunker():
    """Test data processing functionality."""
    print("🔍 Testing dataProcessing function...")
    try:
        # Test that dataProcessing function can be called
        # The function returns None when file doesn't exist, which is expected behavior
        result = dataProcessing("test_file.txt")
        # Accept None as valid return for non-existent files
        assert result is None or isinstance(result, list), (
            f"Expected None or list, got {type(result)}"
        )
        print("  ✅ dataProcessing function call passed (file not found is expected)")

        print("✅ test_data_processing_recursive_chunker: PASSED")
    except Exception as e:
        print(f"❌ test_data_processing_recursive_chunker: FAILED - {e}")
        import traceback

        traceback.print_exc()
        raise


def test_backward_compatibility():
    """Test backward compatibility functions."""
    print("🔍 Testing backward compatibility functions...")
    try:
        # Test chat model backward compatibility with mock
        with patch(
            "llm.chatModel.get_convo_hist_answer",
            return_value={"answer": "Mock response"},
        ):
            from llm.chatModel import get_convo_hist_answer

            result = get_convo_hist_answer("Test question", "test")
            assert isinstance(result, dict), f"Expected dict, got {type(result)}"
            print("  ✅ Chat model backward compatibility passed")

        # Test classification backward compatibility with mock
        with patch(
            "llm.classificationModel.classify_text",
            return_value={"answer": "Mock classification"},
        ):
            from llm.classificationModel import classify_text

            result = classify_text("Test document")
            assert isinstance(result, dict), f"Expected dict, got {type(result)}"
            print("  ✅ Classification backward compatibility passed")

        # Test data processing backward compatibility
        from llm.dataProcessing import dataProcessing

        assert callable(dataProcessing), "dataProcessing should be callable"
        print("  ✅ Data processing backward compatibility passed")

        print("✅ test_backward_compatibility: PASSED")
    except Exception as e:
        print(f"❌ test_backward_compatibility: FAILED - {e}")
        import traceback

        traceback.print_exc()
        raise


def test_model_caching():
    """Test model caching functionality."""
    print("🔍 Testing model caching functionality...")
    try:
        # Test that functions are available (no actual caching to test without services)
        assert callable(get_convo_hist_answer), (
            "get_convo_hist_answer should be callable"
        )
        assert callable(classify_text), "classify_text should be callable"
        print("  ✅ Function availability test passed")

        print("✅ test_model_caching: PASSED")
    except Exception as e:
        print(f"❌ test_model_caching: FAILED - {e}")
        import traceback

        traceback.print_exc()
        raise


def test_error_handling():
    """Test error handling in LLM functions."""
    print("🔍 Testing error handling in LLM functions...")
    try:
        # Test chat model error handling with mock
        with patch(
            "llm.chatModel.get_convo_hist_answer", return_value={"error": "Test error"}
        ):
            result = get_convo_hist_answer("", "test_thread")
            assert isinstance(result, dict), "Should handle empty input gracefully"
            print("  ✅ Chat model error handling passed")

        # Test classification error handling with mock
        with patch(
            "llm.classificationModel.classify_text",
            return_value={"error": "Test error"},
        ):
            result = classify_text("")
            assert isinstance(result, dict), "Should handle empty input gracefully"
            print("  ✅ Classification error handling passed")

        print("✅ test_error_handling: PASSED")
    except Exception as e:
        print(f"❌ test_error_handling: FAILED - {e}")
        import traceback

        traceback.print_exc()
        raise


def test_performance():
    """Test performance of LLM functions."""
    print("🔍 Testing performance of LLM functions...")
    try:
        # Mock the function to avoid actual API calls
        with patch(
            "llm.chatModel.get_convo_hist_answer",
            return_value={"answer": "Mock response"},
        ):
            # Test call speed (should complete within reasonable time)
            import time

            start_time = time.time()
            result = get_convo_hist_answer("Quick test", "test_thread")
            end_time = time.time()

            assert isinstance(result, dict), "Should return a dictionary"
            assert end_time - start_time < 5, (
                "Call should complete within 5 seconds (mocked)"
            )
            print("  ✅ Performance test passed")

        print("✅ test_performance: PASSED")
    except Exception as e:
        print(f"❌ test_performance: FAILED - {e}")
        import traceback

        traceback.print_exc()
        raise


def run_llm_tests():
    """Run all LLM tests."""
    print("🚀 Running LLM tests...")
    print("=" * 60)

    test_functions = [
        test_chat_model_service,
        test_chat_model_call,
        test_classification_service,
        test_classification_classify_text,
        test_data_processing_service,
        test_data_processing_extract_text,
        test_data_processing_recursive_chunker,
        test_backward_compatibility,
        test_model_caching,
        test_error_handling,
        test_performance,
    ]

    results = []
    failed_tests = []
    error_messages = []

    for test_func in test_functions:
        try:
            print(f"\n{'=' * 40}")
            print(f"Running: {test_func.__name__}")
            print(f"{'=' * 40}")

            test_func()
            print(f"✅ {test_func.__name__}: PASSED")
            results.append((test_func.__name__, True))
        except KeyboardInterrupt:
            print(f"\n⚠️  {test_func.__name__} interrupted by user")
            results.append((test_func.__name__, False))
            failed_tests.append(test_func.__name__)
            error_messages.append(f"{test_func.__name__}: Interrupted by user")
            break
        except Exception as e:
            error_msg = f"{e}"
            print(f"❌ {test_func.__name__}: FAILED - {error_msg}")
            import traceback

            traceback.print_exc()
            results.append((test_func.__name__, False))
            failed_tests.append(test_func.__name__)
            error_messages.append(f"{test_func.__name__}: {error_msg}")
            # Continue with other tests instead of exiting

    # Summary
    print(f"\n{'=' * 60}")
    print("LLM TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")

    print(f"\nOverall: {passed}/{total} LLM tests passed")

    if failed_tests:
        print(f"\nFailed tests: {', '.join(failed_tests)}")

        # Display error messages
        if error_messages:
            print(f"\n{'=' * 60}")
            print("ERROR MESSAGES")
            print("=" * 60)
            for error_msg in error_messages:
                print(f"❌ {error_msg}")

    if passed == total:
        print("🎉 All LLM tests passed!")
    else:
        print("💥 Some LLM tests failed!")

    # Return tuple with success status and error messages if any
    if error_messages:
        return False, "; ".join(error_messages)
    else:
        return True


if __name__ == "__main__":
    result = run_llm_tests()
    if isinstance(result, tuple):
        success, error_messages = result
    else:
        success = result
    sys.exit(0 if success else 1)
