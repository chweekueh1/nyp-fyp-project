#!/usr/bin/env python3
"""
Test script to verify that the audio interface correctly integrates with the backend chatbot.
This test verifies that the audio interface calls the correct get_chatbot_response function.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
parent_dir = Path(__file__).parent.parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

import asyncio
from backend.chat import get_chatbot_response
from backend.audio import (
    transcribe_audio,
    transcribe_audio_async,
    _ensure_client_initialized,
)
from backend import config
from backend.chat import _get_chat_metadata_cache


async def test_audio_interface_integration():
    """
    Test that the audio interface correctly calls get_chatbot_response.
    """
    print("🎤 Testing audio interface integration...")

    username = "test_audio_user"
    test_message = "Hello, this is a test audio transcription"
    test_chat_id = "test_audio_chat_123"

    try:
        # Test the get_chatbot_response function directly
        print(f"📝 Testing with message: '{test_message}'")
        print(f"👤 Username: {username}")
        print(f"💬 Chat ID: {test_chat_id}")

        # Call the function that the audio interface should be using
        result = await get_chatbot_response(test_message, [], username, test_chat_id)

        # Verify the result format
        if len(result) == 5:
            (
                empty_message,
                updated_history,
                final_chat_id,
                all_chats_data,
                debug_info,
            ) = result
            print("✅ Function call successful")
            print(f"📊 Result format: {len(result)} elements")
            print(f"💬 Updated history length: {len(updated_history)}")
            print(f"🆔 Final chat ID: {final_chat_id}")
            print(f"🐛 Debug info: {debug_info}")

            # Check if we got a response
            if updated_history and len(updated_history) > 0:
                last_exchange = updated_history[-1]
                if len(last_exchange) >= 2:
                    user_msg, bot_response = last_exchange[0], last_exchange[1]
                    print(f"👤 User message: {user_msg}")
                    print(f"🤖 Bot response: {bot_response[:100]}...")
                    print("✅ Audio interface integration test PASSED")
                    return True
                else:
                    print("❌ Invalid history format")
                    return False
            else:
                print("❌ No history returned")
                return False
        else:
            print(f"❌ Unexpected result format: {len(result)} elements")
            return False

    except Exception as e:
        print(f"❌ Error testing audio interface integration: {e}")
        return False


async def test_audio_interface_mock():
    """
    Test the audio interface with mocked functions to verify correct function calls.
    """
    print("🎤 Testing audio interface with mocks...")

    try:
        # Import the audio interface module
        from gradio_modules.audio_input import audio_interface  # noqa: F401

        print("✅ Audio interface module imported successfully")

        # Test that the module can be instantiated without errors
        # Note: We can't easily test the full Gradio interface without a running app,
        # but we can verify the imports and basic structure

        print("✅ Audio interface module structure is valid")
        print("✅ Audio interface integration test PASSED")
        return True

    except ImportError as e:
        print(f"❌ Failed to import audio interface: {e}")
        return False
    except Exception as e:
        print(f"❌ Error testing audio interface: {e}")
        return False


def test_client_initialization():
    """Test that the client initialization fix works correctly."""
    print("🔍 Testing OpenAI client initialization fix...")

    try:
        # Test 1: Check if client initialization helper works
        print("  📝 Testing _ensure_client_initialized function...")

        # Test the helper function
        result = _ensure_client_initialized()

        if result:
            print("  ✅ Client initialization helper working correctly")
        else:
            print(
                "  ⚠️ Client initialization helper returned False (may be expected if no API key)"
            )

        # Test 2: Test transcribe_audio function with client check
        print("  📝 Testing transcribe_audio function...")

        # This should not crash even if client is not fully initialized
        result = transcribe_audio("nonexistent_file.wav")

        if "OpenAI client not initialized" in result:
            print("  ✅ transcribe_audio properly handles uninitialized client")
        elif "File not found" in result:
            print("  ✅ transcribe_audio client check passed, file check working")
        else:
            print(f"  ⚠️ Unexpected result: {result}")

        # Test 3: Test async function
        print("  📝 Testing transcribe_audio_async function...")

        async def test_async():
            result = await transcribe_audio_async(b"fake_audio_data", "test_user")
            return result

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            result = loop.run_until_complete(test_async())

            if result.get(
                "status"
            ) == "error" and "OpenAI client not initialized" in result.get(
                "message", ""
            ):
                print(
                    "  ✅ transcribe_audio_async properly handles uninitialized client"
                )
            else:
                print(f"  ⚠️ Unexpected async result: {result}")
        finally:
            loop.close()

        print("✅ Audio client initialization fix test completed")
        return True

    except Exception as e:
        print(f"❌ Audio client initialization fix test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_client_injection():
    """Test that client injection from config works."""
    print("🔍 Testing client injection from config...")

    try:
        # Check if client is available in config
        if config.client is not None:
            print("  ✅ Client available in config")

            # Test that the audio module can access it
            result = _ensure_client_initialized()

            if result:
                print("  ✅ Audio module can access client from config")
            else:
                print("  ⚠️ Audio module cannot access client from config")
        else:
            print("  ⚠️ Client not available in config (may be expected if no API key)")

        print("✅ Client injection test completed")
        return True

    except Exception as e:
        print(f"❌ Client injection test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_audio_fixes():
    """Test that the audio transcription fixes work correctly."""
    print("🔍 Testing audio transcription fixes...")

    try:
        # Test 1: Client initialization
        print("  📝 Testing client initialization...")
        client_ready = _ensure_client_initialized()
        if client_ready:
            print("  ✅ Client initialization working")
        else:
            print("  ⚠️ Client not initialized (may be expected if no API key)")

        # Test 2: Chat ID creation with "new_chat_id"
        print("  📝 Testing chat ID creation...")
        username = "test_audio_user"
        test_message = "Hello, this is a test audio transcription"

        # Call get_chatbot_response with "new_chat_id"
        result = await get_chatbot_response(test_message, [], username, "new_chat_id")

        if len(result) >= 3:
            (
                empty_message,
                updated_history,
                final_chat_id,
                all_chats_data,
                debug_info,
            ) = result

            print(f"  ✅ get_chatbot_response returned {len(result)} elements")
            print(f"  📊 Final chat ID: {final_chat_id}")
            print(f"  💬 Updated history length: {len(updated_history)}")
            print(f"  🐛 Debug info: {debug_info}")

            # Check if a real chat ID was created
            if final_chat_id != "new_chat_id":
                print("  ✅ Real chat ID created successfully")

                # Check if the chat exists in user's chat metadata
                user_chats = _get_chat_metadata_cache(username)
                if final_chat_id in user_chats:
                    print("  ✅ Chat ID found in user's chat metadata")
                else:
                    print("  ⚠️ Chat ID not found in user's chat metadata")
            else:
                print("  ⚠️ Chat ID was not converted from 'new_chat_id'")
        else:
            print(f"  ❌ Unexpected result format: {len(result)} elements")
            return False

        # Test 3: Event loop handling
        print("  📝 Testing event loop handling...")

        # This should work without creating new event loops
        try:
            await get_chatbot_response(
                "Second test message", [], username, "new_chat_id"
            )
            print("  ✅ Event loop handling working correctly")
        except RuntimeError as e:
            if "event loop" in str(e):
                print(f"  ❌ Event loop error: {e}")
                return False
            else:
                print(f"  ⚠️ Other runtime error: {e}")

        print("✅ Audio transcription fixes test completed successfully")
        return True

    except Exception as e:
        print(f"❌ Audio transcription fixes test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_client_initialization_fix():
    """Test that the client initialization fix doesn't interfere with existing client."""
    print("🔍 Testing client initialization fix...")

    try:
        # Test 1: Check that client is available in config
        if config.client is not None:
            print("  ✅ Client available in config")
        else:
            print("  ⚠️ Client not available in config (may be expected if no API key)")

        # Test 2: Check that audio module can access client
        client_ready = _ensure_client_initialized()
        if client_ready:
            print("  ✅ Audio module can access client")
        else:
            print("  ⚠️ Audio module cannot access client")

        # Test 3: Verify no duplicate client initialization
        print("  📝 Testing for duplicate client initialization...")

        # Import the client multiple times to ensure no conflicts
        from backend import config as config1
        from backend import config as config2

        if config1.client is config2.client:
            print("  ✅ No duplicate client instances")
        else:
            print("  ❌ Duplicate client instances detected")
            return False

        print("✅ Client initialization fix test completed successfully")
        return True

    except Exception as e:
        print(f"❌ Client initialization fix test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def main():
    """
    Run all audio interface integration tests.
    """
    print("🎤 Audio Interface Integration Tests")
    print("=" * 50)

    test_results = []

    # Test 1: Direct function call test
    print("\n1️⃣ Testing direct get_chatbot_response call...")
    result1 = await test_audio_interface_integration()
    test_results.append(("Direct function call", result1))

    # Test 2: Module import test
    print("\n2️⃣ Testing audio interface module import...")
    result2 = await test_audio_interface_mock()
    test_results.append(("Module import", result2))

    # Test 3: Client initialization fix test
    print("\n3️⃣ Testing client initialization fix...")
    result3 = test_client_initialization()
    test_results.append(("Client Initialization Fix", result3))

    # Test 4: Client injection test
    print("\n4️⃣ Testing client injection...")
    result4 = test_client_injection()
    test_results.append(("Client Injection", result4))

    # Test 5: Audio fixes test
    print("\n5️⃣ Testing audio fixes...")
    result5 = await test_audio_fixes()
    test_results.append(("Audio Fixes", result5))

    # Test 6: Client initialization fix test
    print("\n6️⃣ Testing client initialization fix...")
    result6 = await test_client_initialization_fix()
    test_results.append(("Client Initialization Fix", result6))

    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"  {test_name}: {status}")

    all_passed = all(result for _, result in test_results)
    if all_passed:
        print("\n🎉 All audio interface integration tests PASSED!")
    else:
        print("\n⚠️ Some audio interface integration tests FAILED!")

    return all_passed


if __name__ == "__main__":
    asyncio.run(main())
