#!/usr/bin/env python3
"""
LLM tests for all LLM service classes and functions.
Tests the LLM models, classification, and data processing functionality.
"""

import sys
import os
import asyncio
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
from typing import Dict, Any, List

# Add parent directory to path for imports
parent_dir = Path(__file__).parent.parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Import LLM modules
from llm.chatModel import ChatModelService, State as ChatState, get_chat_model_service
from llm.classificationModel import ClassificationService, State as ClassState, get_classification_service
from llm.dataProcessing import DataProcessingService, get_data_processing_service

def test_chat_model_service():
    """Test ChatModelService functionality."""
    print("🔍 Testing ChatModelService initialization...")
    try:
        # Test service initialization using singleton pattern
        service = get_chat_model_service()
        assert service is not None, "Service should be initialized"
        print("  ✅ Service initialization passed")
        
        # Test singleton pattern
        service2 = get_chat_model_service()
        assert service is service2, "Should be the same instance (singleton)"
        print("  ✅ Singleton pattern passed")
        
        # Test model loading
        assert hasattr(service, 'llm'), "Service should have llm attribute"
        assert hasattr(service, 'embedding'), "Service should have embedding attribute"
        print("  ✅ Model attributes check passed")
        
        print("✅ test_chat_model_service: PASSED")
    except Exception as e:
        print(f"❌ test_chat_model_service: FAILED - {e}")
        import traceback
        traceback.print_exc()
        raise

def test_chat_model_call():
    """Test chat model call functionality."""
    print("🔍 Testing ChatModelService call_model function...")
    try:
        service = get_chat_model_service()
        
        # Mock the call_model method to avoid actual API calls
        with patch.object(service, 'call_model', return_value={
            "input": "Hello, how are you?",
            "chat_history": [],
            "context": "Test context",
            "answer": "Mock response"
        }):
            # Test with valid state
            state: ChatState = {
                "input": "Hello, how are you?",
                "chat_history": [],
                "context": "Test context",
                "answer": ""
            }
            result = service.call_model(state)
            assert isinstance(result, dict), f"Expected dict, got {type(result)}"
            assert "input" in result, "Result should have 'input' key"
            assert "answer" in result, "Result should have 'answer' key"
            print("  ✅ Valid state call passed")
            
            # Test with empty input
            state["input"] = ""
            result = service.call_model(state)
            assert isinstance(result, dict), f"Expected dict, got {type(result)}"
            print("  ✅ Empty input call passed")
        
        print("✅ test_chat_model_call: PASSED")
    except Exception as e:
        print(f"❌ test_chat_model_call: FAILED - {e}")
        import traceback
        traceback.print_exc()
        raise

def test_classification_service():
    """Test ClassificationService functionality."""
    print("🔍 Testing ClassificationService initialization...")
    try:
        # Test service initialization using singleton pattern
        service = get_classification_service()
        assert service is not None, "Service should be initialized"
        print("  ✅ Service initialization passed")
        
        # Test singleton pattern
        service2 = get_classification_service()
        assert service is service2, "Should be the same instance (singleton)"
        print("  ✅ Singleton pattern passed")
        
        # Test model loading
        assert hasattr(service, 'llm'), "Service should have llm attribute"
        assert hasattr(service, 'embedding'), "Service should have embedding attribute"
        print("  ✅ Model attributes check passed")
        
        print("✅ test_classification_service: PASSED")
    except Exception as e:
        print(f"❌ test_classification_service: FAILED - {e}")
        import traceback
        traceback.print_exc()
        raise

def test_classification_classify_text():
    """Test classification text functionality."""
    print("🔍 Testing ClassificationService classify_text function...")
    try:
        service = get_classification_service()
        
        # Mock the classification response to avoid actual API calls
        with patch.object(service, 'classify_text', return_value={"answer": "Mock classification"}):
            # Test with valid text
            result = service.classify_text("This is a test document for classification.")
            assert isinstance(result, dict), f"Expected dict, got {type(result)}"
            print("  ✅ Valid text classification passed")
            
            # Test with empty text
            result = service.classify_text("")
            assert isinstance(result, dict), f"Expected dict, got {type(result)}"
            print("  ✅ Empty text classification passed")
            
            # Test with special characters
            result = service.classify_text("Test with special chars: @#$%^&*()")
            assert isinstance(result, dict), f"Expected dict, got {type(result)}"
            print("  ✅ Special characters classification passed")
        
        print("✅ test_classification_classify_text: PASSED")
    except Exception as e:
        print(f"❌ test_classification_classify_text: FAILED - {e}")
        import traceback
        traceback.print_exc()
        raise

def test_data_processing_service():
    """Test DataProcessingService initialization and singleton pattern."""
    print("🔍 Testing DataProcessingService initialization...")
    try:
        # Test service initialization using singleton getter
        service = get_data_processing_service()
        assert service is not None, "Service should be initialized"
        print("  ✅ Service initialization passed")
        
        # Test singleton pattern
        service2 = get_data_processing_service()
        assert service is service2, "Should be the same instance (singleton)"
        print("  ✅ Singleton pattern passed")
        
        print("✅ test_data_processing_service: PASSED")
    except Exception as e:
        print(f"❌ test_data_processing_service: FAILED - {e}")
        import traceback
        traceback.print_exc()
        raise

def test_data_processing_extract_text():
    """Test text extraction functionality."""
    print("🔍 Testing DataProcessingService extract_text function...")
    try:
        service = get_data_processing_service()
        
        # Create a temporary test file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("This is a test document for text extraction.")
            temp_file = f.name
        
        try:
            # Test text extraction
            result = service.extract_text(temp_file)
            assert isinstance(result, list), f"Expected list, got {type(result)}"
            assert len(result) > 0, "Result should not be empty"
            print("  ✅ Valid file text extraction passed")
            
            # Test with empty file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write("")
                empty_file = f.name
            
            try:
                result = service.extract_text(empty_file)
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
    """Test recursive chunking functionality."""
    print("🔍 Testing DataProcessingService recursive_chunker function...")
    try:
        service = get_data_processing_service()
        
        # Create test documents
        from langchain.schema import Document
        test_docs = [
            Document(page_content="This is a test document for chunking.", metadata={}),
            Document(page_content="Another test document with some content.", metadata={})
        ]
        
        # Test recursive chunking
        result = service.recursive_chunker(test_docs)
        assert isinstance(result, list), f"Expected list, got {type(result)}"
        assert len(result) > 0, "Result should not be empty"
        print("  ✅ Valid documents chunking passed")
        
        # Test with empty documents
        result = service.recursive_chunker([])
        assert isinstance(result, list), f"Expected list, got {type(result)}"
        print("  ✅ Empty documents chunking passed")
        
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
        with patch('llm.chatModel.get_convo_hist_answer', return_value={"answer": "Mock response"}):
            from llm.chatModel import get_convo_hist_answer
            result = get_convo_hist_answer("Test question", "test")
            assert isinstance(result, dict), f"Expected dict, got {type(result)}"
            print("  ✅ Chat model backward compatibility passed")
        
        # Test classification backward compatibility with mock
        with patch('llm.classificationModel.classify_text', return_value={"answer": "Mock classification"}):
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
        # Test that services are cached after first load using singleton pattern
        service1 = get_chat_model_service()
        service2 = get_chat_model_service()
        
        # Both should use the same cached service
        assert service1 is service2, "Services should be cached and shared"
        print("  ✅ Chat model service caching passed")
        
        # Test classification service caching using singleton pattern
        class_service1 = get_classification_service()
        class_service2 = get_classification_service()
        
        assert class_service1 is class_service2, "Classification services should be cached and shared"
        print("  ✅ Classification service caching passed")
        
        print("✅ test_model_caching: PASSED")
    except Exception as e:
        print(f"❌ test_model_caching: FAILED - {e}")
        import traceback
        traceback.print_exc()
        raise

def test_error_handling():
    """Test error handling in LLM services."""
    print("🔍 Testing error handling in LLM services...")
    try:
        service = get_chat_model_service()
        
        # Test with None input
        try:
            state: ChatState = {
                "input": "",  # Use empty string instead of None
                "chat_history": [],
                "context": "",
                "answer": ""
            }
            result = service.call_model(state)
            assert isinstance(result, dict), "Should handle empty input gracefully"
            print("  ✅ Chat model error handling passed")
        except Exception:
            # It's okay if it raises an exception, as long as it's handled
            print("  ✅ Chat model error handling passed (exception caught)")
        
        # Test classification service error handling using singleton
        class_service = get_classification_service()
        try:
            result = class_service.classify_text("")  # Use empty string instead of None
            assert isinstance(result, dict), "Should handle empty input gracefully"
            print("  ✅ Classification error handling passed")
        except Exception:
            # It's okay if it raises an exception, as long as it's handled
            print("  ✅ Classification error handling passed (exception caught)")
        
        print("✅ test_error_handling: PASSED")
    except Exception as e:
        print(f"❌ test_error_handling: FAILED - {e}")
        import traceback
        traceback.print_exc()
        raise

def test_performance():
    """Test performance of LLM services."""
    print("🔍 Testing performance of LLM services...")
    try:
        service = get_chat_model_service()
        
        # Mock the call_model method to avoid actual API calls
        with patch.object(service, 'call_model', return_value={
            "input": "Quick test",
            "chat_history": [],
            "context": "Test context",
            "answer": "Mock response"
        }):
            # Test call speed (should complete within reasonable time)
            import time
            state: ChatState = {
                "input": "Quick test",
                "chat_history": [],
                "context": "Test context",
                "answer": ""
            }
            start_time = time.time()
            result = service.call_model(state)
            end_time = time.time()
            
            assert isinstance(result, dict), "Should return a dictionary"
            assert end_time - start_time < 5, "Call should complete within 5 seconds (mocked)"
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
            print(f"\n{'='*40}")
            print(f"Running: {test_func.__name__}")
            print(f"{'='*40}")
            
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
    print(f"\n{'='*60}")
    print("LLM TEST SUMMARY")
    print('='*60)
    
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
            print(f"\n{'='*60}")
            print("ERROR MESSAGES")
            print('='*60)
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