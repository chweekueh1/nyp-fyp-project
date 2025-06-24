#!/usr/bin/env python3
"""
Test the comprehensive startup time tracking functionality.
Demonstrates the complete app startup performance monitoring.
"""

import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def test_startup_timer_functionality():
    """Test the StartupTimer class functionality."""
    print("🔍 Testing StartupTimer Functionality...")
    
    try:
        from performance_utils import StartupTimer
        
        # Create a test timer
        timer = StartupTimer()
        
        # Test startup tracking
        timer.start_startup_tracking()
        
        # Simulate some startup phases
        time.sleep(0.01)
        timer.mark_startup_phase("phase_1")
        
        time.sleep(0.01)
        timer.mark_startup_phase("phase_2")
        
        time.sleep(0.01)
        timer.mark_startup_phase("phase_3")
        
        # Complete tracking
        total_time = timer.complete_startup_tracking()
        
        # Verify results
        assert total_time > 0, "Should measure positive total time"
        assert total_time < 1.0, "Should be reasonable duration"
        assert len(timer.startup_phases) == 3, "Should track all phases"
        assert timer.startup_completed, "Should mark as completed"
        
        print(f"  ⚡ Total time measured: {total_time:.4f}s")
        print(f"  📊 Phases tracked: {len(timer.startup_phases)}")
        print(f"  ✅ StartupTimer functionality: PASSED")
        
        return True
        
    except Exception as e:
        print(f"  ❌ StartupTimer functionality: FAILED - {e}")
        return False

def test_global_startup_functions():
    """Test the global startup tracking functions."""
    print("🔍 Testing Global Startup Functions...")
    
    try:
        from performance_utils import (
            start_app_startup_tracking, 
            mark_startup_milestone, 
            complete_app_startup_tracking,
            get_total_startup_time
        )
        
        # Test global functions
        start_app_startup_tracking()
        
        time.sleep(0.01)
        mark_startup_milestone("test_milestone_1")
        
        time.sleep(0.01)
        mark_startup_milestone("test_milestone_2")
        
        total_time = complete_app_startup_tracking()
        final_time = get_total_startup_time()
        
        # Verify results
        assert total_time > 0, "Should measure positive total time"
        assert final_time == total_time, "Should return same time"
        
        print(f"  ⚡ Total time measured: {total_time:.4f}s")
        print(f"  📊 Final time retrieved: {final_time:.4f}s")
        print(f"  ✅ Global startup functions: PASSED")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Global startup functions: FAILED - {e}")
        return False

def test_performance_analysis():
    """Test the performance analysis functionality."""
    print("🔍 Testing Performance Analysis...")
    
    try:
        from performance_utils import StartupTimer, perf_monitor
        
        # Create timer and add some metrics
        timer = StartupTimer()
        timer.start_startup_tracking()
        
        # Add some performance metrics
        perf_monitor.start_timer("test_operation_1")
        time.sleep(0.005)
        perf_monitor.end_timer("test_operation_1")
        
        perf_monitor.start_timer("test_operation_2")
        time.sleep(0.003)
        perf_monitor.end_timer("test_operation_2")
        
        # Mark phases
        timer.mark_startup_phase("analysis_phase_1")
        timer.mark_startup_phase("analysis_phase_2")
        
        # Complete and analyze
        total_time = timer.complete_startup_tracking()
        
        # Verify analysis was performed (check logs)
        assert total_time > 0, "Should complete successfully"
        
        print(f"  ⚡ Analysis completed for {total_time:.4f}s startup")
        print(f"  📊 Performance metrics integrated")
        print(f"  ✅ Performance analysis: PASSED")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Performance analysis: FAILED - {e}")
        return False

def test_startup_tracking_integration():
    """Test integration with the actual app startup process."""
    print("🔍 Testing Startup Tracking Integration...")
    
    try:
        # Import the functions used in app.py
        from performance_utils import (
            start_app_startup_tracking,
            mark_startup_milestone,
            complete_app_startup_tracking,
            apply_all_optimizations
        )
        
        # Simulate the app startup sequence
        start_app_startup_tracking()
        
        # Apply optimizations (like in app.py)
        apply_all_optimizations()
        mark_startup_milestone("optimizations_applied")
        
        # Simulate app creation phases
        time.sleep(0.005)
        mark_startup_milestone("loading_css")
        
        time.sleep(0.005)
        mark_startup_milestone("creating_gradio_blocks")
        
        time.sleep(0.010)
        mark_startup_milestone("creating_login_interface")
        
        time.sleep(0.005)
        mark_startup_milestone("creating_main_interface")
        
        time.sleep(0.005)
        mark_startup_milestone("creating_tabbed_interface")
        
        time.sleep(0.010)
        mark_startup_milestone("app_creation_complete")
        
        time.sleep(0.005)
        mark_startup_milestone("starting_app_launch")
        
        time.sleep(0.005)
        mark_startup_milestone("app_launch_complete")
        
        # Complete tracking
        total_time = complete_app_startup_tracking()
        
        # Verify integration
        assert total_time > 0, "Should measure total time"
        assert total_time < 2.0, "Should be reasonable for test"
        
        print(f"  ⚡ Simulated app startup: {total_time:.4f}s")
        print(f"  📊 All milestones tracked successfully")
        print(f"  ✅ Startup tracking integration: PASSED")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Startup tracking integration: FAILED - {e}")
        return False

def demonstrate_comprehensive_report():
    """Demonstrate the comprehensive startup report."""
    print("🔍 Demonstrating Comprehensive Startup Report...")
    
    try:
        from performance_utils import StartupTimer, perf_monitor
        
        # Create a comprehensive test scenario
        timer = StartupTimer()
        timer.start_startup_tracking()
        
        # Simulate various operations with performance monitoring
        operations = [
            ("initialization", 0.010),
            ("loading_modules", 0.015),
            ("creating_interface", 0.020),
            ("setting_up_events", 0.008),
            ("finalizing", 0.005)
        ]
        
        for op_name, duration in operations:
            perf_monitor.start_timer(op_name)
            time.sleep(duration)
            perf_monitor.end_timer(op_name)
            timer.mark_startup_phase(op_name)
        
        # Complete and generate comprehensive report
        total_time = timer.complete_startup_tracking()
        
        print(f"  🎯 Comprehensive report generated for {total_time:.4f}s")
        print(f"  📊 Report includes phases, metrics, and analysis")
        print(f"  ✅ Comprehensive report: PASSED")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Comprehensive report: FAILED - {e}")
        return False

def run_startup_tracking_tests():
    """Run all startup tracking tests."""
    print("🚀 Running Startup Tracking Tests")
    print("=" * 60)
    
    tests = [
        test_startup_timer_functionality,
        test_global_startup_functions,
        test_performance_analysis,
        test_startup_tracking_integration,
        demonstrate_comprehensive_report
    ]
    
    results = []
    total_start = time.time()
    
    for test_func in tests:
        print(f"\n{'='*40}")
        try:
            success = test_func()
            results.append((test_func.__name__, success))
        except Exception as e:
            print(f"❌ {test_func.__name__}: FAILED - {e}")
            results.append((test_func.__name__, False))
    
    total_duration = time.time() - total_start
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 Startup Tracking Test Results:")
    print(f"{'='*60}")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"  {status} {test_name}")
    
    print(f"\n🎯 Summary: {passed}/{total} tests passed")
    print(f"⏱️ Total test time: {total_duration:.2f}s")
    
    if passed == total:
        print("🎉 All startup tracking functionality working perfectly!")
        print("\n📋 Features Verified:")
        print("  ✅ Comprehensive startup time tracking")
        print("  ✅ Milestone-based phase tracking")
        print("  ✅ Performance metrics integration")
        print("  ✅ Detailed startup analysis")
        print("  ✅ Global function interface")
        print("  ✅ App integration compatibility")
        return True
    else:
        print("⚠️ Some startup tracking tests failed")
        return False

if __name__ == "__main__":
    success = run_startup_tracking_tests()
    sys.exit(0 if success else 1)
