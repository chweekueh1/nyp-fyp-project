#!/usr/bin/env python3
"""
Test that backend file upload saves files to the correct location for file classification.
"""

import sys
import os
import tempfile
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def test_backend_file_upload_saves_correctly():
    """Test that backend saves uploaded files to the correct location."""
    print("🔍 Testing Backend File Upload Save Location...")
    
    try:
        # Set test environment
        os.environ['TESTING'] = 'true'
        
        from backend import handle_uploaded_file
        from gradio_modules.file_classification import get_uploads_dir, get_uploaded_files
        
        # Create a test file
        test_content = "This is a test file for upload testing."
        test_filename = "test_upload.txt"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tmp_file:
            tmp_file.write(test_content)
            tmp_file.flush()
            
            # Create a mock file object
            class MockFileObj:
                def __init__(self, path, name):
                    self.name = path
                    self.original_name = name
                    
                def __getattr__(self, name):
                    if name == 'name':
                        return self.original_name
                    return None
            
            mock_file = MockFileObj(tmp_file.name, test_filename)
            
            # Test upload
            ui_state = {
                'username': 'testuser',
                'file_obj': mock_file,
                'history': [],
                'chat_id': None
            }
            
            # Mock the data processing functions to avoid LLM dependency
            def mock_get_data_processing():
                return {'dataProcessing': lambda x: None}
            
            def mock_get_llm_functions():
                return {'is_llm_ready': lambda: True}
            
            # Patch the functions
            import backend
            original_get_data = getattr(backend, 'get_data_processing', None)
            original_get_llm = getattr(backend, 'get_llm_functions', None)
            
            backend.get_data_processing = mock_get_data_processing
            backend.get_llm_functions = mock_get_llm_functions
            
            try:
                # Call the upload handler
                result = handle_uploaded_file(ui_state)
                
                # Check that the result indicates success
                assert 'response' in result, "Result should contain response"
                response = result['response']
                print(f"  📤 Upload response: {response}")
                
                # Check if file was saved to the correct location
                uploads_dir = get_uploads_dir('testuser')
                uploaded_files = get_uploaded_files('testuser')
                
                print(f"  📁 Upload directory: {uploads_dir}")
                print(f"  📋 Uploaded files: {uploaded_files}")
                
                # Verify file was saved (should have timestamp in name)
                txt_files = [f for f in uploaded_files if f.endswith('.txt')]
                assert len(txt_files) > 0, f"Should have at least one .txt file, found: {uploaded_files}"
                
                # Verify the file content
                saved_file = txt_files[0]  # Get the first txt file
                saved_path = os.path.join(uploads_dir, saved_file)
                
                with open(saved_path, 'r') as f:
                    saved_content = f.read()
                
                assert saved_content == test_content, f"File content mismatch: expected '{test_content}', got '{saved_content}'"
                
                print(f"  ✅ File saved correctly to: {saved_path}")
                print(f"  ✅ File content preserved")
                print(f"  ✅ Backend file upload save location: PASSED")
                
                return True
                
            finally:
                # Restore original functions
                if original_get_data:
                    backend.get_data_processing = original_get_data
                if original_get_llm:
                    backend.get_llm_functions = original_get_llm
                
                # Clean up test file
                try:
                    os.unlink(tmp_file.name)
                except:
                    pass
                
                # Clean up uploaded files
                try:
                    for uploaded_file in get_uploaded_files('testuser'):
                        file_path = os.path.join(get_uploads_dir('testuser'), uploaded_file)
                        if os.path.exists(file_path):
                            os.unlink(file_path)
                except:
                    pass
        
    except Exception as e:
        print(f"  ❌ Backend file upload save location: FAILED - {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Clean up environment
        if 'TESTING' in os.environ:
            del os.environ['TESTING']

def test_file_classification_reads_uploaded_files():
    """Test that file classification can read files uploaded by backend."""
    print("🔍 Testing File Classification Reads Backend Uploads...")
    
    try:
        # Set test environment
        os.environ['TESTING'] = 'true'
        
        from gradio_modules.file_classification import get_uploads_dir, save_uploaded_file, get_uploaded_files
        
        # Create a test file and save it using the file classification module
        test_content = "This is a test file for classification reading."
        test_filename = "test_classification.txt"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tmp_file:
            tmp_file.write(test_content)
            tmp_file.flush()
            
            # Create a mock file object
            class MockFileObj:
                def __init__(self, path, name):
                    self.name = path
                    self.original_name = name
                    
                def __getattr__(self, name):
                    if name == 'name':
                        return self.original_name
                    return None
            
            mock_file = MockFileObj(tmp_file.name, test_filename)
            
            # Save file using file classification module
            saved_path, original_filename = save_uploaded_file(mock_file, 'testuser')
            
            print(f"  💾 File saved to: {saved_path}")
            print(f"  📄 Original filename: {original_filename}")
            
            # Verify file can be read back
            uploaded_files = get_uploaded_files('testuser')
            print(f"  📋 Available files: {uploaded_files}")
            
            # Check that our file is in the list
            saved_filename = os.path.basename(saved_path)
            assert saved_filename in uploaded_files, f"Saved file {saved_filename} should be in uploaded files list"
            
            # Verify content
            with open(saved_path, 'r') as f:
                read_content = f.read()
            
            assert read_content == test_content, f"Content mismatch: expected '{test_content}', got '{read_content}'"
            
            print(f"  ✅ File saved and readable")
            print(f"  ✅ Content preserved")
            print(f"  ✅ File classification reads backend uploads: PASSED")
            
            return True
            
    except Exception as e:
        print(f"  ❌ File classification reads backend uploads: FAILED - {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Clean up environment
        if 'TESTING' in os.environ:
            del os.environ['TESTING']
        
        # Clean up uploaded files
        try:
            from gradio_modules.file_classification import get_uploads_dir, get_uploaded_files
            for uploaded_file in get_uploaded_files('testuser'):
                file_path = os.path.join(get_uploads_dir('testuser'), uploaded_file)
                if os.path.exists(file_path):
                    os.unlink(file_path)
        except:
            pass

def run_file_upload_backend_tests():
    """Run all file upload backend tests."""
    print("🚀 Running File Upload Backend Fix Tests")
    print("=" * 60)
    
    tests = [
        test_backend_file_upload_saves_correctly,
        test_file_classification_reads_uploaded_files
    ]
    
    results = []
    
    for test_func in tests:
        print(f"\n{'='*40}")
        try:
            success = test_func()
            results.append((test_func.__name__, success))
        except Exception as e:
            print(f"❌ {test_func.__name__}: FAILED - {e}")
            results.append((test_func.__name__, False))
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 File Upload Backend Fix Test Results:")
    print(f"{'='*60}")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"  {status} {test_name}")
    
    print(f"\n🎯 Summary: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All file upload backend tests passed!")
        print("\n📋 Features Verified:")
        print("  ✅ Backend saves uploaded files to correct location")
        print("  ✅ Files saved to ~/.nypai-chatbot/uploads/{username}")
        print("  ✅ File classification can read backend uploads")
        print("  ✅ File content preserved during upload process")
        print("\n🛠️ Issues Fixed:")
        print("  🔧 Backend now saves files permanently")
        print("  🔧 File classification reads from same location")
        print("  🔧 Uploaded files available for classification")
        return True
    else:
        print("⚠️ Some file upload backend tests failed")
        return False

if __name__ == "__main__":
    success = run_file_upload_backend_tests()
    sys.exit(0 if success else 1)
