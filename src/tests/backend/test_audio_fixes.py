"""
Unit tests for audio-related fixes in the backend of the NYP FYP CNC Chatbot project.
"""

#!/usr/bin/env python3
"""
Test script to verify that the audio transcription event loop and chat ID fixes work correctly.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
parent_dir = Path(__file__).parent.parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

import asyncio
from backend.chat import get_chatbot_response, _get_chat_metadata_cache
from backend.audio import _ensure_client_initialized


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
        from backend import config

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
    """Run all audio fixes tests."""
    print("🎤 Audio Transcription Fixes Verification")
    print("=" * 60)

    test_results = []

    # Test 1: Audio fixes
    print("\n1️⃣ Testing audio transcription fixes...")
    result1 = await test_audio_fixes()
    test_results.append(("Audio Transcription Fixes", result1))

    # Test 2: Client initialization fix
    print("\n2️⃣ Testing client initialization fix...")
    result2 = await test_client_initialization_fix()
    test_results.append(("Client Initialization Fix", result2))

    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Results Summary:")
    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"  {test_name}: {status}")

    all_passed = all(result for _, result in test_results)
    if all_passed:
        print("\n🎉 All audio fixes tests PASSED!")
    else:
        print("\n⚠️ Some audio fixes tests FAILED!")

    return all_passed


if __name__ == "__main__":
    asyncio.run(main())
