#!/usr/bin/env python3
"""
Test script for the clear_chat_history function moved to infra_utils.py
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))


def test_clear_chat_history():
    """Test the clear_chat_history function from infra_utils."""
    print("🧪 Testing clear_chat_history function...")

    try:
        from infra_utils import clear_chat_history, clear_all_chat_history

        # Test with invalid parameters
        print("Testing with invalid chat_id...")
        success, all_chats = clear_chat_history("invalid_chat_id", "test_user")
        assert not success, "Should return False for invalid chat_id"
        assert isinstance(all_chats, dict), "Should return a dict for all_chats"
        print("✅ Invalid chat_id test passed")

        # Test with empty parameters
        print("Testing with empty parameters...")
        success, all_chats = clear_chat_history("", "")
        assert not success, "Should return False for empty parameters"
        print("✅ Empty parameters test passed")

        # Test function signature
        print("Testing function signature...")
        import inspect

        sig = inspect.signature(clear_chat_history)
        assert str(sig) == "(chat_id: str, username: str) -> tuple[bool, dict]", (
            f"Unexpected signature: {sig}"
        )
        print("✅ Function signature test passed")

        # Test clear_all_chat_history exists
        print("Testing clear_all_chat_history function...")
        assert callable(clear_all_chat_history), (
            "clear_all_chat_history should be callable"
        )
        print("✅ clear_all_chat_history test passed")

        print("🎉 All clear_chat_history tests passed!")
        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_clear_chat_history()
    sys.exit(0 if success else 1)
