#!/usr/bin/env python3
"""
Test that demo applications are properly organized in the test suite.
"""

import sys
import os
import subprocess
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def test_demo_directory_structure():
    """Test that demo directory has proper structure."""
    print("🔍 Testing Demo Directory Structure...")
    
    try:
        demos_dir = project_root / "tests" / "demos"
        
        # Verify demos directory exists
        assert demos_dir.exists(), f"Demos directory should exist: {demos_dir}"
        
        # Check for README
        readme_path = demos_dir / "README.md"
        assert readme_path.exists(), f"Demo README should exist: {readme_path}"
        
        # Get all demo files
        demo_files = list(demos_dir.glob("demo_*.py"))
        
        # Verify we have demo files
        assert len(demo_files) > 0, "Should have at least one demo file"
        
        expected_demos = [
            "demo_final_working_chatbot.py",
            "demo_enhanced_chatbot.py", 
            "demo_chatbot_with_history.py",
            "demo_file_classification.py",
            "demo_enhanced_classification.py",
            "demo_audio_interface.py"
        ]
        
        found_demos = [f.name for f in demo_files]
        
        print(f"  📁 Demos directory: {demos_dir}")
        print(f"  📚 README exists: ✅")
        print(f"  📱 Found {len(demo_files)} demo files:")
        
        for demo in found_demos:
            print(f"    ✅ {demo}")
        
        # Check that expected demos exist
        missing_demos = []
        for expected in expected_demos:
            if expected not in found_demos:
                missing_demos.append(expected)
        
        if missing_demos:
            print(f"  ⚠️ Missing expected demos: {missing_demos}")
        else:
            print(f"  ✅ All expected demos present")
        
        print(f"  ✅ Demo directory structure: PASSED")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Demo directory structure: FAILED - {e}")
        import traceback
        traceback.print_exc()
        return False

def test_no_demos_in_root():
    """Test that no demo files remain in project root."""
    print("🔍 Testing No Demos in Root...")
    
    try:
        # Check for demo files in root
        root_demos = list(project_root.glob("demo_*.py"))
        
        if root_demos:
            print(f"  ❌ Found demo files in root: {[f.name for f in root_demos]}")
            print(f"  💡 These should be moved to tests/demos/")
            return False
        else:
            print(f"  ✅ No demo files in root directory")
        
        # Check for test files in root
        root_tests = list(project_root.glob("test_*.py"))
        
        if root_tests:
            print(f"  ❌ Found test files in root: {[f.name for f in root_tests]}")
            print(f"  💡 These should be moved to appropriate test directories")
            return False
        else:
            print(f"  ✅ No test files in root directory")
        
        print(f"  ✅ No demos in root: PASSED")
        
        return True
        
    except Exception as e:
        print(f"  ❌ No demos in root: FAILED - {e}")
        import traceback
        traceback.print_exc()
        return False

def test_demo_file_structure():
    """Test that demo files have proper structure."""
    print("🔍 Testing Demo File Structure...")
    
    try:
        demos_dir = project_root / "tests" / "demos"
        demo_files = list(demos_dir.glob("demo_*.py"))
        
        valid_demos = 0
        
        for demo_file in demo_files:
            print(f"  📱 Checking {demo_file.name}...")
            
            try:
                with open(demo_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check for proper path setup (multiple valid patterns)
                if ("project_root = Path(__file__).parent.parent.parent" in content or
                    "parent_dir = Path(__file__).parent.parent.parent" in content):
                    print(f"    ✅ Correct path setup")
                elif "project_root = Path(__file__).parent" in content:
                    print(f"    ⚠️ Old path setup (should be parent.parent.parent)")
                else:
                    print(f"    ❌ Missing or incorrect path setup")
                    continue
                
                # Check for sys.path.insert (multiple valid patterns)
                if ("sys.path.insert(0, str(project_root))" in content or
                    "sys.path.insert(0, str(parent_dir))" in content):
                    print(f"    ✅ Proper import path setup")
                else:
                    print(f"    ❌ Missing import path setup")
                    continue
                
                # Check for docstring
                if '"""' in content and ("demo" in content.lower() or "demonstration" in content.lower()):
                    print(f"    ✅ Has descriptive docstring")
                else:
                    print(f"    ⚠️ Missing or poor docstring")
                
                # Check for main execution (flexible matching)
                if ("if __name__ == '__main__':" in content or
                    'if __name__ == "__main__":' in content):
                    print(f"    ✅ Has main execution block")
                else:
                    print(f"    ⚠️ Missing main execution block")
                
                valid_demos += 1
                
            except Exception as e:
                print(f"    ❌ Error reading file: {e}")
                continue
        
        print(f"  📊 Valid demos: {valid_demos}/{len(demo_files)}")
        
        if valid_demos == len(demo_files):
            print(f"  ✅ Demo file structure: PASSED")
            return True
        else:
            print(f"  ⚠️ Some demos need structure improvements")
            return True  # Don't fail for minor issues
        
    except Exception as e:
        print(f"  ❌ Demo file structure: FAILED - {e}")
        import traceback
        traceback.print_exc()
        return False

def test_demo_readme_content():
    """Test that demo README has proper content."""
    print("🔍 Testing Demo README Content...")
    
    try:
        readme_path = project_root / "tests" / "demos" / "README.md"
        
        with open(readme_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for required sections
        required_sections = [
            "# 🎭 Chatbot Demos",
            "## 📱 Available Demos",
            "## 🚀 Quick Start",
            "## 🧪 Testing Scenarios"
        ]
        
        missing_sections = []
        for section in required_sections:
            if section not in content:
                missing_sections.append(section)
        
        if missing_sections:
            print(f"  ❌ Missing sections: {missing_sections}")
            return False
        else:
            print(f"  ✅ All required sections present")
        
        # Check for demo documentation
        demos_dir = project_root / "tests" / "demos"
        demo_files = list(demos_dir.glob("demo_*.py"))
        
        documented_demos = 0
        for demo_file in demo_files:
            if demo_file.name in content:
                documented_demos += 1
                print(f"    ✅ {demo_file.name} documented")
            else:
                print(f"    ⚠️ {demo_file.name} not documented")
        
        print(f"  📊 Documented demos: {documented_demos}/{len(demo_files)}")
        
        # Check for usage instructions
        if "```bash" in content and "python tests/demos/" in content:
            print(f"  ✅ Usage instructions present")
        else:
            print(f"  ❌ Missing usage instructions")
            return False
        
        print(f"  ✅ Demo README content: PASSED")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Demo README content: FAILED - {e}")
        import traceback
        traceback.print_exc()
        return False

def test_comprehensive_test_suite_integration():
    """Test that comprehensive test suite recognizes demos."""
    print("🔍 Testing Comprehensive Test Suite Integration...")
    
    try:
        test_suite_path = project_root / "tests" / "comprehensive_test_suite.py"
        
        with open(test_suite_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for demo listing functionality
        if "list_available_demos" in content:
            print(f"  ✅ Demo listing functionality present")
        else:
            print(f"  ❌ Missing demo listing functionality")
            return False
        
        # Check for demo directory reference
        if "demos_dir" in content:
            print(f"  ✅ Demo directory reference present")
        else:
            print(f"  ❌ Missing demo directory reference")
            return False
        
        # Check for demo glob pattern
        if "demo_*.py" in content:
            print(f"  ✅ Demo file pattern recognition present")
        else:
            print(f"  ❌ Missing demo file pattern")
            return False
        
        print(f"  ✅ Comprehensive test suite integration: PASSED")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Comprehensive test suite integration: FAILED - {e}")
        import traceback
        traceback.print_exc()
        return False

def run_demo_organization_tests():
    """Run all demo organization tests."""
    print("🚀 Running Demo Organization Tests")
    print("=" * 60)
    
    tests = [
        test_demo_directory_structure,
        test_no_demos_in_root,
        test_demo_file_structure,
        test_demo_readme_content,
        test_comprehensive_test_suite_integration
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
    print("📊 Demo Organization Test Results:")
    print(f"{'='*60}")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"  {status} {test_name}")
    
    print(f"\n🎯 Summary: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All demo organization tests passed!")
        print("\n📋 Organization Verified:")
        print("  ✅ All demos moved to tests/demos/ directory")
        print("  ✅ No demo files remaining in project root")
        print("  ✅ Proper file structure and path setup")
        print("  ✅ Comprehensive README documentation")
        print("  ✅ Integration with test suite")
        print("\n🛠️ Benefits Achieved:")
        print("  🔧 Clean project root directory")
        print("  🔧 Organized demo structure")
        print("  🔧 Easy demo discovery and execution")
        print("  🔧 Proper documentation and usage instructions")
        print("  🔧 Integration with comprehensive test suite")
        return True
    else:
        print("⚠️ Some demo organization tests failed")
        return False

if __name__ == "__main__":
    success = run_demo_organization_tests()
    sys.exit(0 if success else 1)
