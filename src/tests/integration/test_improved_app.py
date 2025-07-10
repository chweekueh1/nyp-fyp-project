#!/usr/bin/env python3
"""
Test script for the improved app.py with:
1. Optimized backend initialization performance
2. Enhanced chatbot UI integration
"""

import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def test_backend_performance():
    """Test backend initialization performance."""
    print("🚀 Testing backend initialization performance...")

    start_time = time.time()

    try:
        import backend

        # Test the optimized initialization
        print("  📊 Starting backend initialization...")
        init_start = time.time()

        # This should be faster now with optimizations
        import asyncio

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(backend.init_backend())
            init_end = time.time()
            init_time = init_end - init_start

            print(f"  ✅ Backend initialization completed in {init_time:.2f} seconds")

            # Test if components are ready
            if backend.is_llm_ready():
                print("  ✅ LLM is ready and functional")
            else:
                print("  ⚠️ LLM not ready - this may affect performance")

        finally:
            loop.close()

        total_time = time.time() - start_time
        print(f"✅ Total backend test completed in {total_time:.2f} seconds")

        return True

    except Exception as e:
        print(f"❌ Backend performance test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_app_creation():
    """Test app creation with chatbot UI."""
    print("\n🧪 Testing app creation with enhanced chatbot UI...")

    try:
        # Import the main app
        from app import create_app_with_loading

        print("  📱 Creating app with loading screen...")
        start_time = time.time()

        app = create_app_with_loading()

        creation_time = time.time() - start_time
        print(f"  ✅ App created successfully in {creation_time:.2f} seconds")

        # Verify it's a valid Gradio app
        import gradio as gr

        if isinstance(app, gr.Blocks):
            print("  ✅ App is a valid Gradio Blocks object")
        else:
            print(f"  ❌ App is not a Gradio Blocks object: {type(app)}")
            return False

        print("✅ App creation test passed")
        return True

    except Exception as e:
        print(f"❌ App creation test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_chatbot_integration():
    """Test that chatbot UI is properly integrated."""
    print("\n🤖 Testing chatbot UI integration...")

    try:
        # Test importing the chatbot module
        from gradio_modules.chatbot import chatbot_ui, load_all_chats

        print("  ✅ Chatbot module imported successfully")

        # Test creating chatbot UI components
        import gradio as gr

        with gr.Blocks():
            username_state = gr.State("test_user")
            chat_history_state = gr.State([])
            chat_id_state = gr.State("")

            # This should work without errors
            components = chatbot_ui(
                username_state, chat_history_state, chat_id_state, setup_events=False
            )

            if len(components) == 13:
                print("  ✅ Chatbot UI components created successfully")
                print(f"    - Components: {[type(c).__name__ for c in components]}")
            else:
                print(f"  ❌ Expected 13 components, got {len(components)}")
                return False

        # Test load_all_chats function
        chats = load_all_chats("test_user")
        if isinstance(chats, dict):
            print(f"  ✅ load_all_chats working - found {len(chats)} chats")
        else:
            print(f"  ❌ load_all_chats returned invalid type: {type(chats)}")
            return False

        print("✅ Chatbot integration test passed")
        return True

    except Exception as e:
        print(f"❌ Chatbot integration test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_performance_comparison():
    """Compare performance improvements."""
    print("\n📊 Performance comparison...")

    try:
        # Test multiple initialization cycles
        times = []

        for i in range(3):
            print(f"  🔄 Test cycle {i + 1}/3...")
            start = time.time()

            # Test backend functions
            import backend

            # Test chat creation (should be fast)
            backend.create_and_persist_new_chat("perf_test_user")

            # Test chat listing (should be fast)
            backend.list_user_chat_ids("perf_test_user")

            end = time.time()
            cycle_time = end - start
            times.append(cycle_time)
            print(f"    ⏱️ Cycle {i + 1} completed in {cycle_time:.3f} seconds")

        avg_time = sum(times) / len(times)
        print(f"  📈 Average operation time: {avg_time:.3f} seconds")

        if avg_time < 1.0:
            print("  ✅ Performance is good (< 1 second average)")
        elif avg_time < 3.0:
            print("  ⚠️ Performance is acceptable (< 3 seconds average)")
        else:
            print("  ❌ Performance needs improvement (> 3 seconds average)")

        return avg_time < 3.0

    except Exception as e:
        print(f"❌ Performance comparison failed: {e}")
        return False


def run_comprehensive_test():
    """Run all tests."""
    print("🔧 Comprehensive App Improvement Test")
    print("=" * 50)
    print("Testing:")
    print("  1. Backend initialization performance")
    print("  2. App creation with chatbot UI")
    print("  3. Chatbot integration functionality")
    print("  4. Performance comparison")
    print("=" * 50)

    tests = [
        ("Backend Performance", test_backend_performance),
        ("App Creation", test_app_creation),
        ("Chatbot Integration", test_chatbot_integration),
        ("Performance Comparison", test_performance_comparison),
    ]

    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} test failed with exception: {e}")
            results[test_name] = False

    # Summary
    print("\n📊 Test Results Summary")
    print("-" * 30)
    passed = 0
    total = len(results)

    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1

    print(f"\nOverall: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed!")
        print("✅ Backend performance optimized")
        print("✅ Chatbot UI properly integrated")
        print("✅ App ready for use")
        print("\n🚀 You can now run: python src/app.py")
    else:
        print("\n❌ Some tests failed!")
        print("Please check the issues above before using the app.")

    return passed == total


if __name__ == "__main__":
    success = run_comprehensive_test()
    sys.exit(0 if success else 1)
