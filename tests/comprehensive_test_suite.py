#!/usr/bin/env python3
"""
Comprehensive Test Suite for NYP FYP Chatbot Project

This test suite organizes and runs all tests and demos in a structured way:
- Unit Tests: Individual component testing
- Integration Tests: Component interaction testing  
- Feature Tests: Specific feature validation
- Demo Tests: Interactive demonstrations
- Performance Tests: Speed and reliability testing
"""

import sys
import os
import time
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class TestSuite:
    """Comprehensive test suite manager."""
    
    def __init__(self):
        self.project_root = project_root
        self.tests_dir = self.project_root / "tests"
        self.results = {}
        
    def run_test_file(self, test_file: Path, timeout: int = 120) -> Tuple[bool, str, float]:
        """Run a single test file and return results."""
        start_time = time.time()
        
        try:
            print(f"  🧪 Running {test_file.name}...")
            
            result = subprocess.run(
                [sys.executable, str(test_file)],
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=timeout
            )
            
            duration = time.time() - start_time
            
            if result.returncode == 0:
                return True, result.stdout, duration
            else:
                return False, result.stderr or result.stdout, duration
                
        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            return False, f"Test timed out after {timeout} seconds", duration
        except Exception as e:
            duration = time.time() - start_time
            return False, f"Error running test: {str(e)}", duration
    
    def run_unit_tests(self) -> Dict[str, bool]:
        """Run all unit tests."""
        print("\n🔬 Running Unit Tests")
        print("-" * 40)

        unit_tests = [
            self.tests_dir / "frontend" / "test_ui_fixes.py",
            self.tests_dir / "backend" / "test_backend_fixes_and_rename.py",
            self.tests_dir / "backend" / "test_backend.py",
            self.tests_dir / "llm" / "test_llm.py",
        ]
        
        results = {}
        for test_file in unit_tests:
            if test_file.exists():
                success, output, duration = self.run_test_file(test_file)
                results[test_file.name] = success
                
                status = "✅ PASS" if success else "❌ FAIL"
                print(f"    {status} {test_file.name} ({duration:.1f}s)")
                
                if not success:
                    print(f"      Error: {output[:200]}...")
            else:
                print(f"    ⚠️ SKIP {test_file.name} (not found)")
                results[test_file.name] = None
        
        return results
    
    def run_integration_tests(self) -> Dict[str, bool]:
        """Run all integration tests."""
        print("\n🔗 Running Integration Tests")
        print("-" * 40)

        integration_tests = [
            self.tests_dir / "integration" / "test_enhanced_chatbot_features.py",
            self.tests_dir / "integration" / "test_improved_app.py",
            self.tests_dir / "integration" / "test_chatbot_integration.py",
            self.tests_dir / "integration" / "test_main_app_integration.py",
            self.tests_dir / "integration" / "test_main_app_launch.py",
            self.tests_dir / "integration" / "test_integration.py",
        ]
        
        results = {}
        for test_file in integration_tests:
            if test_file.exists():
                success, output, duration = self.run_test_file(test_file)
                results[test_file.name] = success
                
                status = "✅ PASS" if success else "❌ FAIL"
                print(f"    {status} {test_file.name} ({duration:.1f}s)")
                
                if not success:
                    print(f"      Error: {output[:200]}...")
            else:
                print(f"    ⚠️ SKIP {test_file.name} (not found)")
                results[test_file.name] = None
        
        return results
    
    def run_frontend_tests(self) -> Dict[str, bool]:
        """Run all frontend tests."""
        print("\n🎨 Running Frontend Tests")
        print("-" * 40)

        frontend_tests = [
            self.tests_dir / "frontend" / "test_ui_fixes.py",
            self.tests_dir / "frontend" / "test_login_ui.py",
            self.tests_dir / "frontend" / "test_chat_ui.py",
            self.tests_dir / "frontend" / "test_all_interfaces.py",
        ]
        
        results = {}
        for test_file in frontend_tests:
            if test_file.exists():
                success, output, duration = self.run_test_file(test_file)
                results[test_file.name] = success
                
                status = "✅ PASS" if success else "❌ FAIL"
                print(f"    {status} {test_file.name} ({duration:.1f}s)")
                
                if not success:
                    print(f"      Error: {output[:200]}...")
            else:
                print(f"    ⚠️ SKIP {test_file.name} (not found)")
                results[test_file.name] = None
        
        return results
    
    def list_available_demos(self) -> List[Path]:
        """List all available demo files."""
        demo_files = []
        
        # Check demos directory
        demos_dir = self.tests_dir / "demos"
        if demos_dir.exists():
            demo_files.extend(demos_dir.glob("demo_*.py"))
        
        # Check root directory for remaining demos
        demo_files.extend(self.project_root.glob("demo_*.py"))
        
        return sorted(demo_files)
    
    def run_comprehensive_suite(self) -> Dict[str, Dict[str, bool]]:
        """Run the complete test suite."""
        print("🚀 NYP FYP Chatbot - Comprehensive Test Suite")
        print("=" * 60)
        print(f"Project Root: {self.project_root}")
        print(f"Python Version: {sys.version}")
        print("=" * 60)
        
        all_results = {}
        
        # Run different test categories
        all_results["unit_tests"] = self.run_unit_tests()
        all_results["integration_tests"] = self.run_integration_tests()
        all_results["frontend_tests"] = self.run_frontend_tests()
        
        # List available demos
        print("\n🎭 Available Demos")
        print("-" * 40)
        demos = self.list_available_demos()
        if demos:
            for demo in demos:
                print(f"    📱 {demo.name}")
            print(f"\n    Run demos individually: python {demos[0].parent}/demo_name.py")
        else:
            print("    No demo files found")
        
        return all_results
    
    def print_summary(self, results: Dict[str, Dict[str, bool]]):
        """Print comprehensive test summary."""
        print("\n📊 Test Suite Summary")
        print("=" * 60)
        
        total_passed = 0
        total_failed = 0
        total_skipped = 0
        
        for category, category_results in results.items():
            print(f"\n{category.replace('_', ' ').title()}:")
            
            passed = sum(1 for r in category_results.values() if r is True)
            failed = sum(1 for r in category_results.values() if r is False)
            skipped = sum(1 for r in category_results.values() if r is None)
            
            total_passed += passed
            total_failed += failed
            total_skipped += skipped
            
            print(f"  ✅ Passed: {passed}")
            print(f"  ❌ Failed: {failed}")
            print(f"  ⚠️ Skipped: {skipped}")
        
        print(f"\n🎯 Overall Results:")
        print(f"  ✅ Total Passed: {total_passed}")
        print(f"  ❌ Total Failed: {total_failed}")
        print(f"  ⚠️ Total Skipped: {total_skipped}")
        
        success_rate = (total_passed / (total_passed + total_failed)) * 100 if (total_passed + total_failed) > 0 else 0
        print(f"  📈 Success Rate: {success_rate:.1f}%")
        
        if total_failed == 0:
            print("\n🎉 All tests passed! The chatbot is ready for use.")
        else:
            print(f"\n⚠️ {total_failed} test(s) failed. Please review the issues above.")
        
        return total_failed == 0

def main():
    """Run the comprehensive test suite."""
    suite = TestSuite()
    results = suite.run_comprehensive_suite()
    success = suite.print_summary(results)
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
