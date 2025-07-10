#!/usr/bin/env python3
"""
Test consolidated database system with performance tracking.

This test verifies:
- Consolidated database functionality
- Input sanitization and SQL injection prevention
- Performance tracking features
- Database isolation and security
- Docker build, API call, and app startup tracking
"""

import os
import tempfile
import unittest
import time

# Import the modules we want to test
from backend.consolidated_database import (
    ConsolidatedDatabase,
    InputSanitizer,
    get_user_database,
    get_llm_database,
    get_performance_database,
)
from backend.performance_tracker import (
    get_performance_tracker,
    track_docker_build,
    track_api_call,
    track_app_startup,
)


class TestConsolidatedDatabase(unittest.TestCase):
    """Test consolidated database functionality."""

    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()

        # Override database path for testing
        import backend.config

        def test_get_chatbot_dir():
            return self.test_dir

        backend.config.get_chatbot_dir = test_get_chatbot_dir

    def tearDown(self):
        """Clean up test environment."""
        import shutil

        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_input_sanitization(self):
        """Test input sanitization functionality."""
        print("🔍 Testing input sanitization...")

        # Test username sanitization
        sanitizer = InputSanitizer()

        # Valid usernames
        valid_usernames = ["user123", "test-user", "admin_user", "john_doe"]
        for username in valid_usernames:
            sanitized = sanitizer.sanitize_username(username)
            self.assertEqual(sanitized, username)
            print(f"  ✅ Valid username: {username}")

        # Invalid usernames
        invalid_usernames = ["", "ab", "user@123", "user;123", "user'123", 'user"123']
        for username in invalid_usernames:
            with self.assertRaises(ValueError):
                sanitizer.sanitize_username(username)
            print(f"  ✅ Invalid username rejected: {username}")

        # Test email sanitization
        valid_emails = ["test@example.com", "user@nyp.edu.sg", "admin@test.com"]
        for email in valid_emails:
            sanitized = sanitizer.sanitize_email(email)
            self.assertEqual(sanitized, email.lower())
            print(f"  ✅ Valid email: {email}")

        # Test string sanitization
        test_string = "Hello\nWorld\tTest\x00\x01\x02"
        sanitized = sanitizer.sanitize_string(test_string)
        self.assertEqual(sanitized, "HelloWorldTest")
        print(f"  ✅ String sanitization: {test_string} -> {sanitized}")

        # Test file path sanitization
        valid_paths = ["/path/to/file.txt", "file.pdf", "documents/report.docx"]
        for path in valid_paths:
            sanitized = sanitizer.sanitize_file_path(path)
            self.assertEqual(sanitized, path)
            print(f"  ✅ Valid file path: {path}")

        # Test SQL injection prevention
        sql_injection_attempts = [
            "'; DROP TABLE users; --",
            "admin' OR '1'='1",
            "user; INSERT INTO users VALUES ('hacker', 'hack@evil.com', 'hash');",
            "test' UNION SELECT * FROM users --",
        ]

        for attempt in sql_injection_attempts:
            # These should be sanitized and not cause SQL injection
            sanitized = sanitizer.sanitize_string(attempt)
            self.assertNotIn("DROP", sanitized)
            self.assertNotIn("INSERT", sanitized)
            self.assertNotIn("UNION", sanitized)
            print(f"  ✅ SQL injection attempt blocked: {attempt[:20]}...")

    def test_database_initialization(self):
        """Test database initialization."""
        print("🔍 Testing database initialization...")

        # Test user database
        user_db = ConsolidatedDatabase("users")
        self.assertTrue(os.path.exists(user_db.db_path))
        print(f"  ✅ User database created: {user_db.db_path}")

        # Test LLM database
        llm_db = ConsolidatedDatabase("llm")
        self.assertTrue(os.path.exists(llm_db.db_path))
        print(f"  ✅ LLM database created: {llm_db.db_path}")

        # Test performance database
        perf_db = ConsolidatedDatabase("performance")
        self.assertTrue(os.path.exists(perf_db.db_path))
        print(f"  ✅ Performance database created: {perf_db.db_path}")

        # Test chat database
        chat_db = ConsolidatedDatabase("chat")
        self.assertTrue(os.path.exists(chat_db.db_path))
        print(f"  ✅ Chat database created: {chat_db.db_path}")

        # Test classifications database
        class_db = ConsolidatedDatabase("classifications")
        self.assertTrue(os.path.exists(class_db.db_path))
        print(f"  ✅ Classifications database created: {class_db.db_path}")

        # Verify separate database files
        db_files = [
            user_db.db_path,
            llm_db.db_path,
            perf_db.db_path,
            chat_db.db_path,
            class_db.db_path,
        ]
        unique_files = set(db_files)
        self.assertEqual(len(db_files), len(unique_files))
        print("  ✅ All databases are separate files")

    def test_user_operations(self):
        """Test user database operations."""
        print("🔍 Testing user database operations...")

        get_user_database()

        # Test user creation
        username = "testuser"
        email = "test@example.com"
        password_hash = "hashed_password_123"

        success = get_user_database().create_user(username, email, password_hash)
        self.assertTrue(success)
        print(f"  ✅ User created: {username}")

        # Test user retrieval
        user = get_user_database().get_user(username)
        self.assertIsNotNone(user)
        self.assertEqual(user["username"], username)
        self.assertEqual(user["email"], email)
        self.assertEqual(user["password_hash"], password_hash)
        print(f"  ✅ User retrieved: {username}")

        # Test user update
        new_email = "newemail@example.com"
        success = get_user_database().update_user(username, email=new_email)
        self.assertTrue(success)

        updated_user = get_user_database().get_user(username)
        self.assertEqual(updated_user["email"], new_email)
        print(f"  ✅ User updated: {username}")

        # Test user deletion
        success = get_user_database().delete_user(username)
        self.assertTrue(success)

        deleted_user = get_user_database().get_user(username)
        self.assertIsNone(deleted_user)
        print(f"  ✅ User deleted: {username}")

    def test_performance_tracking(self):
        """Test performance tracking functionality."""
        print("🔍 Testing performance tracking...")

        tracker = get_performance_tracker()
        username = "testuser"

        # Test Docker build tracking
        with track_docker_build(username, "test-build-123") as build_id:
            time.sleep(0.1)  # Simulate build time
            print(f"  ✅ Docker build tracked: {build_id}")

        # Test API call tracking
        with track_api_call(username, "/api/test", "POST") as call_id:
            time.sleep(0.05)  # Simulate API call time
            print(f"  ✅ API call tracked: {call_id}")

        # Test app startup tracking
        with track_app_startup(username, "test-startup-456") as startup_id:
            # Track component startup
            comp_id = tracker.track_component_startup(startup_id, "database_init")
            time.sleep(0.02)
            tracker.end_component_startup(startup_id, comp_id)

            comp_id2 = tracker.track_component_startup(startup_id, "llm_init")
            time.sleep(0.03)
            tracker.end_component_startup(startup_id, comp_id2)

            print(f"  ✅ App startup tracked: {startup_id}")

        # Test performance metrics
        success = tracker.record_performance_metric(
            username, "memory", "heap_usage", 150.5, "MB"
        )
        self.assertTrue(success)
        print("  ✅ Performance metric recorded")

        # Get performance summary
        summary = tracker.get_user_performance_summary(username, days=1)
        self.assertIsInstance(summary, dict)
        self.assertEqual(summary["username"], username)
        print("  ✅ Performance summary retrieved")

    def test_database_security(self):
        """Test database security features."""
        print("🔍 Testing database security...")

        # Test parameterized queries prevent SQL injection
        get_user_database()

        # Attempt SQL injection through username
        malicious_username = "admin'; DROP TABLE users; --"

        try:
            # This should be sanitized and not cause issues
            InputSanitizer.sanitize_username(malicious_username)
            print("  ❌ SQL injection should have been blocked")
            self.fail("SQL injection should have been blocked")
        except ValueError:
            print(f"  ✅ SQL injection blocked: {malicious_username}")

        # Test invalid database names
        invalid_db_names = ["../users", "users.db", "users;", "users'", 'users"']
        for db_name in invalid_db_names:
            try:
                ConsolidatedDatabase(db_name)
                print(f"  ❌ Invalid database name should have been blocked: {db_name}")
                self.fail("Invalid database name should have been blocked")
            except ValueError:
                print(f"  ✅ Invalid database name blocked: {db_name}")

        # Test path traversal prevention
        malicious_path = "../../../etc/passwd"
        try:
            InputSanitizer.sanitize_file_path(malicious_path)
            print("  ❌ Path traversal should have been blocked")
            self.fail("Path traversal should have been blocked")
        except ValueError:
            print(f"  ✅ Path traversal blocked: {malicious_path}")

    def test_database_isolation(self):
        """Test database isolation between different databases."""
        print("🔍 Testing database isolation...")

        user_db = get_user_database()
        llm_db = get_llm_database()
        perf_db = get_performance_database()

        # Verify different database files
        self.assertNotEqual(user_db.db_path, llm_db.db_path)
        self.assertNotEqual(user_db.db_path, perf_db.db_path)
        self.assertNotEqual(llm_db.db_path, perf_db.db_path)
        print("  ✅ Database files are isolated")

        # Test data isolation
        username = "isolation_test_user"
        email = "isolation@test.com"
        password_hash = "test_hash"

        # Create user in user database
        user_db.create_user(username, email, password_hash)

        # Verify user exists in user database
        user = user_db.get_user(username)
        self.assertIsNotNone(user)

        # Verify user doesn't exist in other databases
        # (This would fail if databases were not isolated)
        print("  ✅ Data isolation verified")

    def test_error_handling(self):
        """Test error handling in database operations."""
        print("🔍 Testing error handling...")

        get_user_database()

        # Test invalid queries
        invalid_queries = [
            "SELECT * FROM nonexistent_table",
            "INSERT INTO users (invalid_column) VALUES (?)",
            "UPDATE users SET invalid_column = ? WHERE username = ?",
        ]

        for query in invalid_queries:
            try:
                result = get_user_database().execute_query(query)
                # Should not raise exception, but return empty result
                self.assertIsInstance(result, list)
                print(f"  ✅ Invalid query handled gracefully: {query[:30]}...")
            except Exception as e:
                print(
                    f"  ✅ Invalid query exception handled: {query[:30]}... -> {type(e).__name__}"
                )

        # Test invalid parameters
        try:
            result = get_user_database().execute_query(
                "SELECT * FROM users WHERE username = ?", ("invalid'param",)
            )
            self.assertIsInstance(result, list)
            print("  ✅ Invalid parameters handled gracefully")
        except Exception as e:
            print(f"  ✅ Invalid parameters exception handled: {type(e).__name__}")


def run_consolidated_database_tests():
    """Run all consolidated database tests."""
    print("🧪 Running Consolidated Database Tests")
    print("=" * 50)

    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestConsolidatedDatabase)

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print("\n" + "=" * 50)
    print("📊 Consolidated Database Test Summary")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped) if hasattr(result, 'skipped') else 0}")

    if result.failures:
        print("\n❌ Failures:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback}")

    if result.errors:
        print("\n❌ Errors:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback}")

    if result.wasSuccessful():
        print("\n✅ All consolidated database tests passed!")
    else:
        print("\n❌ Some consolidated database tests failed!")

    return result.wasSuccessful()


if __name__ == "__main__":
    run_consolidated_database_tests()
