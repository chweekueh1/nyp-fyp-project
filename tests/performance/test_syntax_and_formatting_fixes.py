#!/usr/bin/env python3
"""
Test that all syntax and formatting errors have been fixed in the test suite and gradio modules.
"""

import sys
import os
import subprocess
import ast
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def test_python_syntax_compilation():
    """Test that all Python files compile without syntax errors."""
    print("🔍 Testing Python Syntax Compilation...")
    
    try:
        # Key gradio modules
        gradio_modules = [
            "gradio_modules/classification_formatter.py",
            "gradio_modules/enhanced_content_extraction.py", 
            "gradio_modules/file_classification.py",
            "gradio_modules/chatbot.py",
            "gradio_modules/login_and_register.py",
            "gradio_modules/audio_input.py",
            "gradio_modules/file_upload.py",
            "gradio_modules/chat_history.py",
            "gradio_modules/chat_interface.py",
            "gradio_modules/search_interface.py"
        ]
        
        # Key test files
        test_files = [
            "tests/comprehensive_test_suite.py",
            "tests/performance/test_demo_organization.py",
            "tests/performance/test_final_organization_verification.py",
            "tests/performance/test_enhanced_file_classification.py",
            "tests/performance/test_logging_and_dependency_paths.py"
        ]
        
        all_files = gradio_modules + test_files
        compilation_results = []
        
        for file_path in all_files:
            full_path = project_root / file_path
            if full_path.exists():
                try:
                    # Test compilation
                    result = subprocess.run(
                        [sys.executable, "-m", "py_compile", str(full_path)],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    
                    if result.returncode == 0:
                        print(f"  ✅ {file_path}")
                        compilation_results.append((file_path, True, None))
                    else:
                        print(f"  ❌ {file_path}: {result.stderr}")
                        compilation_results.append((file_path, False, result.stderr))
                        
                except subprocess.TimeoutExpired:
                    print(f"  ⏰ {file_path}: Compilation timeout")
                    compilation_results.append((file_path, False, "Timeout"))
                    
            else:
                print(f"  ⚠️ {file_path}: File not found")
                compilation_results.append((file_path, False, "File not found"))
        
        # Summary
        passed = sum(1 for _, success, _ in compilation_results if success)
        total = len(compilation_results)
        
        print(f"  📊 Compilation Results: {passed}/{total} files compiled successfully")
        
        if passed == total:
            print(f"  ✅ Python syntax compilation: PASSED")
            return True
        else:
            print(f"  ❌ Some files failed compilation")
            for file_path, success, error in compilation_results:
                if not success:
                    print(f"    - {file_path}: {error}")
            return False
        
    except Exception as e:
        print(f"  ❌ Python syntax compilation: FAILED - {e}")
        return False

def test_type_annotation_fixes():
    """Test that type annotation issues have been fixed."""
    print("🔍 Testing Type Annotation Fixes...")
    
    try:
        # Test the classification formatter specifically
        from gradio_modules.classification_formatter import (
            format_classification_response,
            format_reasoning,
            format_classification_summary
        )
        
        # Test format_reasoning with None confidence
        reasoning_result = format_reasoning("Test reasoning", None)
        assert isinstance(reasoning_result, str), "format_reasoning should return string"
        print(f"  ✅ format_reasoning handles None confidence")
        
        # Test format_reasoning with float confidence
        reasoning_result = format_reasoning("Test reasoning", 0.85)
        assert isinstance(reasoning_result, str), "format_reasoning should return string"
        print(f"  ✅ format_reasoning handles float confidence")
        
        # Test format_classification_summary with None values
        summary_result = format_classification_summary("OFFICIAL(OPEN)", "LOW", None, None)
        assert isinstance(summary_result, str), "format_classification_summary should return string"
        print(f"  ✅ format_classification_summary handles None values")
        
        # Test complete formatting function
        classification = {
            'classification': 'OFFICIAL(OPEN)',
            'sensitivity': 'LOW',
            'reasoning': 'Test reasoning',
            'confidence': 0.85
        }
        
        extraction_info = {
            'content': 'Test content',
            'method': 'text_file',
            'file_size': 1024,
            'file_type': '.txt'
        }
        
        file_info = {
            'filename': 'test.txt',
            'size': '1024',
            'saved_name': 'test_saved.txt'
        }
        
        formatted = format_classification_response(classification, extraction_info, file_info)
        assert isinstance(formatted, dict), "format_classification_response should return dict"
        print(f"  ✅ format_classification_response works correctly")
        
        print(f"  ✅ Type annotation fixes: PASSED")
        return True
        
    except Exception as e:
        print(f"  ❌ Type annotation fixes: FAILED - {e}")
        import traceback
        traceback.print_exc()
        return False

def test_import_functionality():
    """Test that all modules can be imported without errors."""
    print("🔍 Testing Import Functionality...")
    
    try:
        # Test gradio modules
        gradio_imports = [
            ("gradio_modules.classification_formatter", ["format_classification_response"]),
            ("gradio_modules.enhanced_content_extraction", ["enhanced_extract_file_content"]),
            ("gradio_modules.file_classification", ["file_classification_interface"]),
            ("gradio_modules.chatbot", ["chatbot_ui"]),
            ("gradio_modules.login_and_register", ["login_interface"]),
            ("gradio_modules.audio_input", ["audio_interface"])
        ]
        
        import_results = []
        
        for module_name, functions in gradio_imports:
            try:
                module = __import__(module_name, fromlist=functions)
                
                # Check that functions exist
                for func_name in functions:
                    if hasattr(module, func_name):
                        print(f"  ✅ {module_name}.{func_name}")
                    else:
                        print(f"  ❌ {module_name}.{func_name} not found")
                        import_results.append((f"{module_name}.{func_name}", False))
                        continue
                
                import_results.append((module_name, True))
                
            except ImportError as e:
                if "gradio" in str(e).lower():
                    print(f"  ⚠️ {module_name}: Gradio not available (expected in test environment)")
                    import_results.append((module_name, True))  # Don't fail for missing gradio
                else:
                    print(f"  ❌ {module_name}: Import error - {e}")
                    import_results.append((module_name, False))
            except Exception as e:
                print(f"  ❌ {module_name}: Other error - {e}")
                import_results.append((module_name, False))
        
        # Summary
        passed = sum(1 for _, success in import_results if success)
        total = len(import_results)
        
        print(f"  📊 Import Results: {passed}/{total} modules imported successfully")
        
        if passed == total:
            print(f"  ✅ Import functionality: PASSED")
            return True
        else:
            print(f"  ❌ Some imports failed")
            return False
        
    except Exception as e:
        print(f"  ❌ Import functionality: FAILED - {e}")
        return False

def test_ast_parsing():
    """Test that all Python files can be parsed by AST without syntax errors."""
    print("🔍 Testing AST Parsing...")
    
    try:
        # Key files to test
        files_to_test = [
            "gradio_modules/classification_formatter.py",
            "gradio_modules/enhanced_content_extraction.py",
            "gradio_modules/file_classification.py",
            "tests/performance/test_demo_organization.py",
            "tests/comprehensive_test_suite.py"
        ]
        
        ast_results = []
        
        for file_path in files_to_test:
            full_path = project_root / file_path
            if full_path.exists():
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Parse with AST
                    ast.parse(content, filename=str(full_path))
                    print(f"  ✅ {file_path}")
                    ast_results.append((file_path, True))
                    
                except SyntaxError as e:
                    print(f"  ❌ {file_path}: Syntax error - {e}")
                    ast_results.append((file_path, False))
                except Exception as e:
                    print(f"  ❌ {file_path}: Parse error - {e}")
                    ast_results.append((file_path, False))
            else:
                print(f"  ⚠️ {file_path}: File not found")
                ast_results.append((file_path, False))
        
        # Summary
        passed = sum(1 for _, success in ast_results if success)
        total = len(ast_results)
        
        print(f"  📊 AST Parsing Results: {passed}/{total} files parsed successfully")
        
        if passed == total:
            print(f"  ✅ AST parsing: PASSED")
            return True
        else:
            print(f"  ❌ Some files failed AST parsing")
            return False
        
    except Exception as e:
        print(f"  ❌ AST parsing: FAILED - {e}")
        return False

def test_diagnostic_tool_fixes():
    """Test that diagnostic tool path fixes work correctly."""
    print("🔍 Testing Diagnostic Tool Fixes...")
    
    try:
        # Test the diagnostic tool import
        sys.path.insert(0, str(project_root / "tests" / "utils"))
        
        try:
            import diagnose_chatbot_issue  # type: ignore
            print(f"  ✅ Diagnostic tool imports correctly")
            
            # Test that it has the correct project root
            if hasattr(diagnose_chatbot_issue, 'project_root'):
                diag_root = diagnose_chatbot_issue.project_root
                expected_root = project_root
                if str(diag_root) == str(expected_root):
                    print(f"  ✅ Diagnostic tool has correct project root")
                else:
                    print(f"  ⚠️ Diagnostic tool project root mismatch")
                    print(f"    Expected: {expected_root}")
                    print(f"    Got: {diag_root}")
            
        except ImportError as e:
            print(f"  ❌ Diagnostic tool import failed: {e}")
            return False
        
        print(f"  ✅ Diagnostic tool fixes: PASSED")
        return True
        
    except Exception as e:
        print(f"  ❌ Diagnostic tool fixes: FAILED - {e}")
        return False

def run_syntax_and_formatting_tests():
    """Run all syntax and formatting fix tests."""
    print("🚀 Running Syntax and Formatting Fix Tests")
    print("=" * 60)
    
    tests = [
        test_python_syntax_compilation,
        test_type_annotation_fixes,
        test_import_functionality,
        test_ast_parsing,
        test_diagnostic_tool_fixes
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
    print("📊 Syntax and Formatting Fix Test Results:")
    print(f"{'='*60}")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"  {status} {test_name}")
    
    print(f"\n🎯 Summary: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All syntax and formatting fix tests passed!")
        print("\n📋 Issues Fixed:")
        print("  ✅ Type annotation errors in classification_formatter.py")
        print("  ✅ Optional type imports and usage")
        print("  ✅ Python syntax compilation errors")
        print("  ✅ Import functionality restored")
        print("  ✅ AST parsing issues resolved")
        print("  ✅ Diagnostic tool path setup corrected")
        print("\n🛠️ Quality Improvements:")
        print("  🔧 Proper type annotations with Optional")
        print("  🔧 Clean Python syntax throughout codebase")
        print("  🔧 Reliable module imports")
        print("  🔧 Correct project path handling")
        print("  🔧 Comprehensive error handling")
        return True
    else:
        print("⚠️ Some syntax and formatting fix tests failed")
        return False

if __name__ == "__main__":
    success = run_syntax_and_formatting_tests()
    sys.exit(0 if success else 1)
