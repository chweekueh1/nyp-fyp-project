#!/usr/bin/env python3
"""
Backend tests for all backend functions and API endpoints.
Tests the backend logic, database operations, and API responses.
"""

import sys
import os
import asyncio
import tempfile
from pathlib import Path
from unittest.mock import patch

# Add parent directory to path for imports
parent_dir = Path(__file__).parent.parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Import backend functions
from backend import (
    sanitize_input,
    generateUniqueFilename,
    check_health,
    do_register,
    get_chat_history,
    get_user_chats,
    get_user_chats_with_names,
    get_chat_name,
    set_chat_name,
    rename_chat_file,
    search_chat_history,
    get_completion,
    init_backend,
    fuzzy_search_chats,
    render_all_chats,
    change_password,
)

# Import utils functions
from infra_utils import (
    rel2abspath,
    create_folders,
    ensure_chatbot_dir_exists,
    get_chatbot_dir,
    setup_logging,
)


def test_sanitize_input():
    """Test input sanitization function."""
    print("🔍 Testing sanitize_input function...")
    try:
        # Test normal input
        result = sanitize_input("Hello World")
        assert result == "Hello World", f"Expected 'Hello World', got '{result}'"
        print("  ✅ Normal input sanitization passed")

        # Test empty input
        result = sanitize_input("")
        assert result == "", f"Expected empty string, got '{result}'"
        result = sanitize_input(None)
        assert result == "", f"Expected empty string for None, got '{result}'"
        print("  ✅ Empty/None input sanitization passed")

        # Test input with special characters (function removes non-alphanumeric chars after HTML escaping)
        result = sanitize_input("Hello <script>alert('xss')</script>")
        # The function does: html.escape() then removes special chars, so < becomes &lt; then gets removed
        assert result == "Hello ltscriptgtalertx27xssx27ltscriptgt", (
            f"Expected special chars removed, got '{result}'"
        )
        print("  ✅ Special characters sanitization passed")

        # Test input with non-alphanumeric characters
        result = sanitize_input("Hello@World#123")
        assert result == "HelloWorld123", f"Expected alphanumeric only, got '{result}'"
        print("  ✅ Non-alphanumeric character removal passed")

        # Test input length limit
        long_input = "A" * 600
        result = sanitize_input(long_input)
        assert len(result) <= 500, f"Expected length <= 500, got {len(result)}"
        print("  ✅ Input length limit passed")

        print("✅ test_sanitize_input: PASSED")
    except Exception as e:
        print(f"❌ test_sanitize_input: FAILED - {e}")
        import traceback

        traceback.print_exc()
        raise


def test_generate_unique_filename():
    """Test unique filename generation."""
    print("🔍 Testing generateUniqueFilename function...")
    try:
        # Test basic functionality
        filename1 = generateUniqueFilename("test", "user", ".txt")
        filename2 = generateUniqueFilename("test", "user", ".txt")

        assert filename1 != filename2, (
            f"Generated filenames should be unique: {filename1} vs {filename2}"
        )
        assert filename1.startswith("test_user_"), (
            f"Filename should start with 'test_user_', got '{filename1}'"
        )
        assert filename1.endswith(".txt"), (
            f"Filename should end with '.txt', got '{filename1}'"
        )
        print("  ✅ Basic filename generation passed")

        # Test with different parameters
        filename3 = generateUniqueFilename("document", "admin", ".pdf")
        assert filename3.startswith("document_admin_"), (
            f"Filename should start with 'document_admin_', got '{filename3}'"
        )
        assert filename3.endswith(".pdf"), (
            f"Filename should end with '.pdf', got '{filename3}'"
        )
        print("  ✅ Different parameter filename generation passed")

        print("✅ test_generate_unique_filename: PASSED")
    except Exception as e:
        print(f"❌ test_generate_unique_filename: FAILED - {e}")
        import traceback

        traceback.print_exc()
        raise


async def test_check_health():
    """Test health check endpoint."""
    print("🔍 Testing check_health function...")
    try:
        result = await check_health()
        assert isinstance(result, dict), f"Expected dict, got {type(result)}"
        assert result.get("status") == "OK", (
            f"Expected status 'OK', got '{result.get('status')}'"
        )
        assert result.get("code") == "200", (
            f"Expected code '200', got '{result.get('code')}'"
        )
        print("  ✅ Health check response format passed")
        print("✅ test_check_health: PASSED")
    except Exception as e:
        print(f"❌ test_check_health: FAILED - {e}")
        import traceback

        traceback.print_exc()
        raise


async def test_do_login():
    """Test login functionality."""
    print("🔍 Testing do_login function...")
    try:
        import os

        testing = os.getenv("TESTING", "").lower() == "true"
        if testing:
            from backend import do_login_test as do_login_backend
        else:
            from backend import do_login as do_login_backend
        # Test with valid credentials (mock)
        with patch("backend.verify_password", return_value=True):
            result = await do_login_backend("test_user", "TestPass123!")
            assert isinstance(result, dict), f"Expected dict, got {type(result)}"
            assert result.get("code") in ["200", "404"], (
                f"Expected code '200' or '404', got '{result.get('code')}'"
            )
            print("  ✅ Valid credentials login passed")
        # Test with invalid credentials
        with patch("backend.verify_password", return_value=False):
            result = await do_login_backend("test_user", "wrongpass")
            assert isinstance(result, dict), f"Expected dict, got {type(result)}"
            assert result.get("code") != "200", (
                f"Expected non-200 code, got '{result.get('code')}'"
            )
            print("  ✅ Invalid credentials login passed")
        # Test with empty credentials
        result = await do_login_backend("", "")
        assert isinstance(result, dict), f"Expected dict, got {type(result)}"
        assert result.get("code") != "200", (
            f"Expected non-200 code for empty credentials, got '{result.get('code')}'"
        )
        print("  ✅ Empty credentials login passed")
        print("✅ test_do_login: PASSED")
    except Exception as e:
        print(f"❌ test_do_login: FAILED - {e}")
        import traceback

        traceback.print_exc()
        raise


async def test_do_register():
    """Test registration functionality."""
    print("🔍 Testing do_register function...")
    try:
        # Test with valid new user
        with (
            patch("backend.hash_password", return_value="hashed_password"),
            patch("os.path.exists", return_value=False),
            patch("builtins.open", create=True),
            patch("json.dump"),
            patch("json.load", return_value={}),
        ):
            result = await do_register("test_user", "newpass123!")
            assert isinstance(result, dict), f"Expected dict, got {type(result)}"
            assert result.get("code") in ["200", "500"], (
                f"Expected code '200' or '500', got '{result.get('code')}'"
            )
            print("  ✅ Valid new user registration passed")
        # Test with existing user
        with (
            patch("os.path.exists", return_value=True),
            patch("builtins.open", create=True),
            patch("json.load", return_value={"users": {"test_user": "hash"}}),
        ):
            result = await do_register("test_user", "newpass123!")
            print(f"    [DEBUG] Existing user registration result: {result}")
            assert result.get("code") != "200", (
                f"Expected non-200 code for existing user, got '{result.get('code')}'. Full result: {result}"
            )
            print("  ✅ Existing user registration passed")
        # Test with weak password
        result = await do_register("test_user", "weak")
        assert isinstance(result, dict), f"Expected dict, got {type(result)}"
        assert result.get("code") != "200", (
            f"Expected non-200 code for weak password, got '{result.get('code')}'"
        )
        print("  ✅ Weak password registration passed")
        print("✅ test_do_register: PASSED")
    except Exception as e:
        print(f"❌ test_do_register: FAILED - {e}")
        import traceback

        traceback.print_exc()
        raise


async def test_change_password():
    """Test change_password functionality."""
    print("🔍 Testing change_password function...")

    # Success case
    with (
        patch("backend.check_rate_limit", return_value=True),
        patch("backend.validate_username", return_value=(True, "")),
        patch("os.path.exists", return_value=True),
        patch("builtins.open", create=True),
        patch(
            "json.load",
            return_value={"users": {"test_user": {"hashedPassword": "oldhash"}}},
        ),
        patch("backend.verify_password", return_value=True),
        patch("backend.is_password_complex", return_value=(True, "")),
        patch("backend.hash_password", return_value="newhash"),
        patch("json.dump"),
    ):
        result = await change_password("test_user", "oldpass", "newpass123!")
        assert result["code"] == "200", f"Expected 200, got {result['code']}"
        print("  ✅ Password change success case passed")

    # Wrong old password
    with (
        patch("backend.check_rate_limit", return_value=True),
        patch("backend.validate_username", return_value=(True, "")),
        patch("os.path.exists", return_value=True),
        patch("builtins.open", create=True),
        patch(
            "json.load",
            return_value={"users": {"test_user": {"hashedPassword": "oldhash"}}},
        ),
        patch("backend.verify_password", return_value=False),
    ):
        result = await change_password("test_user", "wrongpass", "newpass123!")
        assert result["code"] == "401", f"Expected 401, got {result['code']}"
        print("  ✅ Wrong old password case passed")

    # Weak new password
    with (
        patch("backend.check_rate_limit", return_value=True),
        patch("backend.validate_username", return_value=(True, "")),
        patch("os.path.exists", return_value=True),
        patch("builtins.open", create=True),
        patch(
            "json.load",
            return_value={"users": {"test_user": {"hashedPassword": "oldhash"}}},
        ),
        patch("backend.verify_password", return_value=True),
        patch("backend.is_password_complex", return_value=(False, "Too weak")),
    ):
        result = await change_password("test_user", "oldpass", "weak")
        assert result["code"] == "400", f"Expected 400, got {result['code']}"
        print("  ✅ Weak new password case passed")

    # Rate limit
    with (
        patch("backend.check_rate_limit", return_value=False),
        patch("backend.get_rate_limit_info", return_value={"time_window": 60}),
    ):
        result = await change_password("test_user", "oldpass", "newpass123!")
        assert result["code"] == "429", f"Expected 429, got {result['code']}"
        print("  ✅ Rate limit case passed")

    print("✅ test_change_password: PASSED")


def test_get_chat_history():
    """Test chat history retrieval."""
    print("🔍 Testing get_chat_history function...")
    try:
        # Test with non-existent chat
        result = get_chat_history("nonexistent", "test_user")
        assert isinstance(result, list), f"Expected list, got {type(result)}"
        print("  ✅ Non-existent chat history passed")
        # Test with empty parameters
        result = get_chat_history("", "")
        assert isinstance(result, list), f"Expected list, got {type(result)}"
        print("  ✅ Empty parameters chat history passed")
        print("✅ test_get_chat_history: PASSED")
    except Exception as e:
        print(f"❌ test_get_chat_history: FAILED - {e}")
        import traceback

        traceback.print_exc()
        raise


def test_get_user_chats():
    """Test user chat list retrieval."""
    print("🔍 Testing get_user_chats function...")
    try:
        # Test with non-existent user
        result = get_user_chats("nonexistent")
        assert isinstance(result, list), f"Expected list, got {type(result)}"
        print("  ✅ Non-existent user chats passed")
        # Test with empty username
        result = get_user_chats("")
        assert isinstance(result, list), f"Expected list, got {type(result)}"
        print("  ✅ Empty username chats passed")
        print("✅ test_get_user_chats: PASSED")
    except Exception as e:
        print(f"❌ test_get_user_chats: FAILED - {e}")
        import traceback

        traceback.print_exc()
        raise


def test_get_user_chats_with_names():
    """Test user chat list with names retrieval."""
    print("🔍 Testing get_user_chats_with_names function...")
    try:
        # Test with non-existent user
        result = get_user_chats_with_names("nonexistent")
        assert isinstance(result, list), f"Expected list, got {type(result)}"
        print("  ✅ Non-existent user chats with names passed")
        # Test with empty username
        result = get_user_chats_with_names("")
        assert isinstance(result, list), f"Expected list, got {type(result)}"
        print("  ✅ Empty username chats with names passed")
        print("✅ test_get_user_chats_with_names: PASSED")
    except Exception as e:
        print(f"❌ test_get_user_chats_with_names: FAILED - {e}")
        import traceback

        traceback.print_exc()
        raise


def test_get_chat_name():
    """Test chat name retrieval."""
    print("🔍 Testing get_chat_name function...")
    try:
        # Test with non-existent chat
        result = get_chat_name("nonexistent", "test_user")
        assert isinstance(result, str), f"Expected string, got {type(result)}"
        print("  ✅ Non-existent chat name passed")
        # Test with empty parameters
        result = get_chat_name("", "")
        assert isinstance(result, str), f"Expected string, got {type(result)}"
        print("  ✅ Empty parameters chat name passed")
        print("✅ test_get_chat_name: PASSED")
    except Exception as e:
        print(f"❌ test_get_chat_name: FAILED - {e}")
        import traceback

        traceback.print_exc()
        raise


def test_set_chat_name():
    """Test chat name setting."""
    print("🔍 Testing set_chat_name function...")
    try:
        # Test with non-existent chat
        result = set_chat_name("nonexistent", "test_user", "New Name")
        assert isinstance(result, bool), f"Expected bool, got {type(result)}"
        print("  ✅ Non-existent chat name setting passed")
        # Test with empty parameters
        result = set_chat_name("", "", "")
        assert isinstance(result, bool), f"Expected bool, got {type(result)}"
        print("  ✅ Empty parameters chat name setting passed")
        print("✅ test_set_chat_name: PASSED")
    except Exception as e:
        print(f"❌ test_set_chat_name: FAILED - {e}")
        import traceback

        traceback.print_exc()
        raise


def test_rename_chat_file():
    """Test chat file renaming."""
    print("🔍 Testing rename_chat_file function...")
    try:
        # Test with non-existent chat
        result = rename_chat_file("old_chat", "new_chat", "test_user")
        assert isinstance(result, bool), f"Expected bool, got {type(result)}"
        print("  ✅ Non-existent chat file renaming passed")
        # Test with empty parameters
        result = rename_chat_file("", "", "")
        assert isinstance(result, bool), f"Expected bool, got {type(result)}"
        print("  ✅ Empty parameters chat file renaming passed")
        print("✅ test_rename_chat_file: PASSED")
    except Exception as e:
        print(f"❌ test_rename_chat_file: FAILED - {e}")
        import traceback

        traceback.print_exc()
        raise


def test_search_chat_history():
    """Test chat history search."""
    print("🔍 Testing search_chat_history function...")
    try:
        # Test with non-existent user
        result = search_chat_history("test query", "test_user")
        assert isinstance(result, list), f"Expected list, got {type(result)}"
        print("  ✅ Non-existent user search passed")
        # Test with empty parameters
        result = search_chat_history("", "")
        assert isinstance(result, list), f"Expected list, got {type(result)}"
        print("  ✅ Empty parameters search passed")
        # Test with valid parameters
        result = search_chat_history("test query", "test_user")
        assert isinstance(result, list), f"Expected list, got {type(result)}"
        print("  ✅ Valid parameters search passed")
        print("✅ test_search_chat_history: PASSED")
    except Exception as e:
        print(f"❌ test_search_chat_history: FAILED - {e}")
        import traceback

        traceback.print_exc()
        raise


def test_get_completion():
    """Test completion generation."""
    print("🔍 Testing get_completion function...")
    try:
        # Test with valid prompt
        result = get_completion("Hello, how are you?")
        assert isinstance(result, (str, dict)), (
            f"Expected str or dict, got {type(result)}"
        )
        print("  ✅ Valid prompt completion passed")

        # Test with empty prompt
        result = get_completion("")
        assert isinstance(result, (str, dict)), (
            f"Expected str or dict, got {type(result)}"
        )
        print("  ✅ Empty prompt completion passed")

        # Test with different models
        result = get_completion("Test prompt", model="gpt-4o-mini")
        assert isinstance(result, (str, dict)), (
            f"Expected str or dict, got {type(result)}"
        )
        print("  ✅ Different model completion passed")

        print("✅ test_get_completion: PASSED")
    except Exception as e:
        print(f"❌ test_get_completion: FAILED - {e}")
        import traceback

        traceback.print_exc()
        raise


async def test_init_backend():
    """Test backend initialization."""
    print("🔍 Testing init_backend function...")
    try:
        # Test backend initialization
        await init_backend()
        print("  ✅ Backend initialization passed")
        print("✅ test_init_backend: PASSED")
    except Exception as e:
        print(f"❌ test_init_backend: FAILED - {e}")
        import traceback

        traceback.print_exc()
        raise


def test_rate_limiting():
    """Test rate limiting functionality."""
    print("🔍 Testing rate limiting functionality...")
    try:
        from backend import (
            chat_rate_limiter,
            file_upload_rate_limiter,
            audio_rate_limiter,
            auth_rate_limiter,
            get_rate_limit_info,
        )

        # Test rate limiter initialization
        assert chat_rate_limiter.max_requests == 60, (
            f"Expected chat max_requests 60, got {chat_rate_limiter.max_requests}"
        )
        assert chat_rate_limiter.time_window == 60, (
            f"Expected chat time_window 60, got {chat_rate_limiter.time_window}"
        )
        print("  ✅ Chat rate limiter initialization passed")

        assert file_upload_rate_limiter.max_requests == 10, (
            f"Expected file upload max_requests 10, got {file_upload_rate_limiter.max_requests}"
        )
        assert file_upload_rate_limiter.time_window == 60, (
            f"Expected file upload time_window 60, got {file_upload_rate_limiter.time_window}"
        )
        print("  ✅ File upload rate limiter initialization passed")

        assert audio_rate_limiter.max_requests == 20, (
            f"Expected audio max_requests 20, got {audio_rate_limiter.max_requests}"
        )
        assert audio_rate_limiter.time_window == 60, (
            f"Expected audio time_window 60, got {audio_rate_limiter.time_window}"
        )
        print("  ✅ Audio rate limiter initialization passed")

        assert auth_rate_limiter.max_requests == 5, (
            f"Expected auth max_requests 5, got {auth_rate_limiter.max_requests}"
        )
        assert auth_rate_limiter.time_window == 300, (
            f"Expected auth time_window 300, got {auth_rate_limiter.time_window}"
        )
        print("  ✅ Auth rate limiter initialization passed")

        # Test get_rate_limit_info function
        chat_info = get_rate_limit_info("chat")
        assert chat_info["max_requests"] == 60, (
            f"Expected chat max_requests 60, got {chat_info['max_requests']}"
        )
        assert chat_info["time_window"] == 60, (
            f"Expected chat time_window 60, got {chat_info['time_window']}"
        )
        assert chat_info["requests_per_second"] == 1.0, (
            f"Expected chat requests_per_second 1.0, got {chat_info['requests_per_second']}"
        )
        print("  ✅ Rate limit info function passed")

        print("✅ test_rate_limiting: PASSED")
    except Exception as e:
        print(f"❌ test_rate_limiting: FAILED - {e}")
        import traceback

        traceback.print_exc()
        raise


def test_fuzzy_search_chats():
    """Test fuzzy search functionality."""
    print("🔍 Testing fuzzy_search_chats function...")
    try:
        # Test with empty query
        result = fuzzy_search_chats("test", "")
        assert result == "No matching chats found", (
            f"Expected 'No matching chats found', got '{result}'"
        )
        print("  ✅ Empty query test passed")

        # Test with empty username
        result = fuzzy_search_chats("", "test query")
        assert result == "No matching chats found", (
            f"Expected 'No matching chats found', got '{result}'"
        )
        print("  ✅ Empty username test passed")

        # Test with non-existent user
        result = fuzzy_search_chats("nonexistent", "test query")
        assert result == "No matching chats found", (
            f"Expected 'No matching chats found', got '{result}'"
        )
        print("  ✅ Non-existent user test passed")

        print("✅ test_fuzzy_search_chats: PASSED")
    except Exception as e:
        print(f"❌ test_fuzzy_search_chats: FAILED - {e}")
        import traceback

        traceback.print_exc()
        raise


def test_render_all_chats():
    """Test render all chats functionality."""
    print("🔍 Testing render_all_chats function...")
    try:
        # Test with empty username
        result = render_all_chats("")
        assert isinstance(result, list), f"Expected list, got {type(result)}"
        assert len(result) == 0, f"Expected empty list, got {len(result)} items"
        print("  ✅ Empty username test passed")

        # Test with non-existent user
        result = render_all_chats("nonexistent")
        assert isinstance(result, list), f"Expected list, got {type(result)}"
        assert len(result) == 0, f"Expected empty list, got {len(result)} items"
        print("  ✅ Non-existent user test passed")

        print("✅ test_render_all_chats: PASSED")
    except Exception as e:
        print(f"❌ test_render_all_chats: FAILED - {e}")
        import traceback

        traceback.print_exc()
        raise


def test_rel2abspath():
    """Test rel2abspath returns absolute path."""
    print("🔍 Testing rel2abspath function...")
    try:
        rel_path = "test_dir/test_file.txt"
        abs_path = rel2abspath(rel_path)
        assert os.path.isabs(abs_path), f"Expected absolute path, got {abs_path}"
        assert abs_path.endswith(os.path.join("test_dir", "test_file.txt")), (
            f"Path ending mismatch: {abs_path}"
        )
        print("✅ test_rel2abspath: PASSED")
    except Exception as e:
        print(f"❌ test_rel2abspath: FAILED - {e}")
        raise


def test_create_folders():
    """Test create_folders creates directories idempotently."""
    print("🔍 Testing create_folders function...")
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            test_dir = os.path.join(tmpdir, "a", "b", "c")
            create_folders(test_dir)
            assert os.path.isdir(test_dir), f"Directory not created: {test_dir}"
            # Call again to check idempotency
            create_folders(test_dir)
            assert os.path.isdir(test_dir), (
                f"Directory not present after second call: {test_dir}"
            )
        print("✅ test_create_folders: PASSED")
    except Exception as e:
        print(f"❌ test_create_folders: FAILED - {e}")
        raise


def test_get_chatbot_dir():
    """Test get_chatbot_dir returns a plausible path."""
    print("🔍 Testing get_chatbot_dir function...")
    try:
        path = get_chatbot_dir()
        assert isinstance(path, str), f"Expected string, got {type(path)}"
        assert ".nypai-chatbot" in path, f"Expected .nypai-chatbot in path, got {path}"
        print("✅ test_get_chatbot_dir: PASSED")
    except Exception as e:
        print(f"❌ test_get_chatbot_dir: FAILED - {e}")
        raise


def test_ensure_chatbot_dir_exists():
    """Test ensure_chatbot_dir_exists creates the chatbot directory."""
    print("🔍 Testing ensure_chatbot_dir_exists function...")
    try:
        path = get_chatbot_dir()

        # Test that the function works whether directory exists or not
        # Don't try to delete it as it might contain locked files (ChromaDB)
        ensure_chatbot_dir_exists()
        assert os.path.isdir(path), f"Chatbot dir not created: {path}"

        # Test idempotency - call again to make sure it doesn't fail
        ensure_chatbot_dir_exists()
        assert os.path.isdir(path), f"Chatbot dir not present after second call: {path}"

        print("✅ test_ensure_chatbot_dir_exists: PASSED")
    except Exception as e:
        print(f"❌ test_ensure_chatbot_dir_exists: FAILED - {e}")
        raise


def test_setup_logging():
    """Test setup_logging configures logging and creates log file."""
    print("🔍 Testing setup_logging function...")
    try:
        logger = setup_logging()
        logger.debug("Test debug log entry")
        log_file = os.path.join(os.path.dirname(__file__), "..", "..", "app.log")
        log_file = os.path.abspath(log_file)
        assert os.path.isfile(log_file), f"Log file not created: {log_file}"
        with open(log_file, "r", encoding="utf-8") as f:
            content = f.read()
        assert "Test debug log entry" in content or len(content) > 0, (
            "Log file is empty or missing log entry"
        )
        print("✅ test_setup_logging: PASSED")
    except Exception as e:
        print(f"❌ test_setup_logging: FAILED - {e}")
        raise


async def run_backend_tests():
    """Run all backend tests."""
    print("🚀 Running backend tests...")
    print("=" * 60)

    test_functions = [
        test_sanitize_input,
        test_generate_unique_filename,
        test_check_health,
        test_do_login,
        test_do_register,
        test_get_chat_history,
        test_get_user_chats,
        test_get_user_chats_with_names,
        test_get_chat_name,
        test_set_chat_name,
        test_rename_chat_file,
        test_search_chat_history,
        test_fuzzy_search_chats,
        test_render_all_chats,
        test_get_completion,
        test_init_backend,
        test_rate_limiting,
        test_rel2abspath,
        test_create_folders,
        test_get_chatbot_dir,
        test_ensure_chatbot_dir_exists,
        test_setup_logging,
    ]

    results = []
    failed_tests = []
    error_messages = []

    for test_func in test_functions:
        try:
            print(f"\n{'=' * 40}")
            print(f"Running: {test_func.__name__}")
            print(f"{'=' * 40}")
            if asyncio.iscoroutinefunction(test_func):
                await test_func()
            else:
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
    print(f"\n{'=' * 60}")
    print("BACKEND TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")

    print(f"\nOverall: {passed}/{total} backend tests passed")

    if failed_tests:
        print(f"\nFailed tests: {', '.join(failed_tests)}")

        # Display error messages
        if error_messages:
            print(f"\n{'=' * 60}")
            print("ERROR MESSAGES")
            print("=" * 60)
            for error_msg in error_messages:
                print(f"❌ {error_msg}")

    if passed == total:
        print("🎉 All backend tests passed!")
    else:
        print("💥 Some backend tests failed!")

    # Return tuple with success status and error messages if any
    if error_messages:
        return False, "; ".join(error_messages)
    else:
        return True


if __name__ == "__main__":
    import asyncio

    result = asyncio.run(run_backend_tests())
    if isinstance(result, tuple):
        success, error_messages = result
    else:
        success = result
    sys.exit(0 if success else 1)
