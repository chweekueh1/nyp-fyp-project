#!/usr/bin/env python3
"""
Test script for change password functionality.
"""

import gradio as gr
import sys
from pathlib import Path
import os

# Add parent directory to path for imports
parent_dir = Path(__file__).parent.parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Import backend functions directly
testing = os.getenv("TESTING", "").lower() == "true"
if testing:
    from backend import change_password as backend_change_password
else:
    from backend import change_password as backend_change_password


def test_change_password_interface():
    """Test the complete change password interface with all features."""
    with gr.Blocks(title="Change Password Interface Test") as app:
        # Header
        gr.Markdown("# Change Password Interface Test")

        # Import and create change password interface
        from gradio_modules.change_password import change_password_interface

        # Create states
        username_state = gr.State("test_user")
        logged_in_state = gr.State(True)

        # Create change password interface
        change_password_btn, change_password_popup, last_change_time = (
            change_password_interface(username_state, logged_in_state)
        )

        # Status display
        gr.Markdown("## Test Instructions")
        gr.Markdown("""
        **Test the following:**
        1. **Change Password Button:** Click to open the popup
        2. **Password Toggles:** Click the eye icons to show/hide passwords
        3. **Form Validation:** Try submitting with empty fields
        4. **Password Mismatch:** Enter different passwords in new and confirm fields
        5. **Successful Change:** Use current password: `TestPass123!` and new password: `NewPass456!`
        6. **Cancel Button:** Click to close the popup without changes

        **Expected Behavior:**
        - Change password button should open a popup
        - Password toggles should show/hide password text
        - Form should validate all required fields
        - Password mismatch should show error
        - Successful change should show success message and trigger logout
        - Cancel should close the popup
        """)

    return app


def test_simple_change_password():
    """Test a simplified change password interface for basic functionality."""

    async def handle_change_password(
        username, old_password, new_password, confirm_password
    ):
        """Handle password change using backend function directly."""
        print(
            f"Password change attempt: {username}, old: {old_password}, new: {new_password}"
        )
        try:
            # Validate inputs
            if not old_password or not new_password or not confirm_password:
                return "❌ All fields are required."

            if new_password != confirm_password:
                return "❌ New passwords do not match."

            # Call backend function directly
            result = await backend_change_password(username, old_password, new_password)
            print(f"Backend change password result: {result}")

            if result.get("code") == "200":
                return "✅ Password changed successfully. You will be logged out."
            else:
                return f"❌ Password change failed: {result.get('message', 'Unknown error')}"
        except Exception as e:
            print(f"Password change error: {e}")
            return f"❌ Password change error: {str(e)}"

    def toggle_password_visibility(current_visible, password_type):
        """Toggle password visibility for different password fields."""
        print(f"Toggle {password_type} password visibility: {current_visible}")
        return not current_visible, "text" if not current_visible else "password"

    with gr.Blocks(title="Simple Change Password Test") as app:
        gr.Markdown("# Simple Change Password Test")

        # States
        old_password_visible = gr.State(False)
        new_password_visible = gr.State(False)
        confirm_password_visible = gr.State(False)

        # Input fields
        username = gr.Textbox(
            label="Username",
            placeholder="Enter username",
            value="test_user",
            interactive=False,
        )
        old_password = gr.Textbox(
            label="Current Password",
            placeholder="Enter current password",
            type="password",
        )
        new_password = gr.Textbox(
            label="New Password", placeholder="Enter new password", type="password"
        )
        confirm_password = gr.Textbox(
            label="Confirm New Password",
            placeholder="Confirm new password",
            type="password",
        )

        # Toggle buttons
        with gr.Row():
            old_toggle_btn = gr.Button("👁️ Old Password", size="sm")
            new_toggle_btn = gr.Button("👁️ New Password", size="sm")
            confirm_toggle_btn = gr.Button("👁️ Confirm Password", size="sm")

        # Action buttons
        with gr.Row():
            change_btn = gr.Button("Change Password", variant="primary")
            cancel_btn = gr.Button("Cancel", variant="secondary")

        # Output
        result = gr.Markdown("Enter credentials and click buttons to test...")

        # Password requirements info
        gr.Markdown("""
        **Password Requirements:**
        - At least 8 characters long
        - Contains uppercase and lowercase letters
        - Contains at least one number
        - Contains at least one special character (!@#$%^&*)
        """)

        # Event handlers
        change_btn.click(
            fn=handle_change_password,
            inputs=[username, old_password, new_password, confirm_password],
            outputs=[result],
            api_name="simple_change_password",
        )

        old_toggle_btn.click(
            fn=toggle_password_visibility,
            inputs=[old_password_visible, gr.State("old")],
            outputs=[old_password_visible, old_password],
            api_name="toggle_old_password",
        )

        new_toggle_btn.click(
            fn=toggle_password_visibility,
            inputs=[new_password_visible, gr.State("new")],
            outputs=[new_password_visible, new_password],
            api_name="toggle_new_password",
        )

        confirm_toggle_btn.click(
            fn=toggle_password_visibility,
            inputs=[confirm_password_visible, gr.State("confirm")],
            outputs=[confirm_password_visible, confirm_password],
            api_name="toggle_confirm_password",
        )

        cancel_btn.click(
            fn=lambda: "Popup closed",
            outputs=[result],
            api_name="cancel_change_password",
        )

        # Instructions
        gr.Markdown("""
        **Test Instructions:**
        1. **Current Password:** Enter `TestPass123!`
        2. **New Password:** Enter `NewPass456!`
        3. **Confirm Password:** Enter `NewPass456!`
        4. Click **Change Password** - should show success message
        5. Try **Password Toggles** - should show/hide password text
        6. Try **Cancel** - should clear the result
        7. Test validation by leaving fields empty or mismatching passwords

        **Expected Behavior:**
        - All buttons should be clickable
        - Password change should work with valid credentials
        - Password toggles should work for all fields
        - Form validation should work
        - Backend function should be called directly
        """)

    return app


def test_change_password_validation():
    """Test password change validation scenarios."""

    async def test_validation_scenario(
        scenario, username, old_password, new_password, confirm_password
    ):
        """Test different validation scenarios."""
        print(f"Testing scenario: {scenario}")

        # Basic validation
        if not old_password or not new_password or not confirm_password:
            return f"❌ Scenario {scenario}: All fields are required."

        if new_password != confirm_password:
            return f"❌ Scenario {scenario}: New passwords do not match."

        try:
            result = await backend_change_password(username, old_password, new_password)
            if result.get("code") == "200":
                return f"✅ Scenario {scenario}: Password changed successfully."
            else:
                return (
                    f"❌ Scenario {scenario}: {result.get('message', 'Unknown error')}"
                )
        except Exception as e:
            return f"❌ Scenario {scenario}: Error - {str(e)}"

    with gr.Blocks(title="Change Password Validation Test") as app:
        gr.Markdown("# Change Password Validation Test")

        # Test scenarios
        scenarios = gr.Dropdown(
            choices=[
                "Empty fields",
                "Password mismatch",
                "Wrong current password",
                "Weak new password",
                "Same password",
                "Valid password change",
            ],
            label="Select Test Scenario",
            value="Valid password change",
        )

        # Input fields
        username = gr.Textbox(label="Username", value="test_user", interactive=False)
        old_password = gr.Textbox(label="Current Password", type="password")
        new_password = gr.Textbox(label="New Password", type="password")
        confirm_password = gr.Textbox(label="Confirm New Password", type="password")

        # Test button
        test_btn = gr.Button("Run Test Scenario", variant="primary")

        # Results
        result = gr.Markdown("Select a scenario and click 'Run Test Scenario'")

        def update_fields_for_scenario(scenario):
            """Update input fields based on selected scenario."""
            if scenario == "Empty fields":
                return "", "", ""
            elif scenario == "Password mismatch":
                return "TestPass123!", "NewPass456!", "DifferentPass789!"
            elif scenario == "Wrong current password":
                return "WrongPass123!", "NewPass456!", "NewPass456!"
            elif scenario == "Weak new password":
                return "TestPass123!", "weak", "weak"
            elif scenario == "Same password":
                return "TestPass123!", "TestPass123!", "TestPass123!"
            elif scenario == "Valid password change":
                return "TestPass123!", "NewPass456!", "NewPass456!"
            else:
                return "TestPass123!", "NewPass456!", "NewPass456!"

        test_btn.click(
            fn=test_validation_scenario,
            inputs=[scenarios, username, old_password, new_password, confirm_password],
            outputs=[result],
            api_name="test_validation",
        )

        scenarios.change(
            fn=update_fields_for_scenario,
            inputs=[scenarios],
            outputs=[old_password, new_password, confirm_password],
            api_name="update_scenario_fields",
        )

        # Instructions
        gr.Markdown("""
        **Test Scenarios:**
        1. **Empty fields:** Tests form validation
        2. **Password mismatch:** Tests confirm password validation
        3. **Wrong current password:** Tests authentication
        4. **Weak new password:** Tests password complexity requirements
        5. **Same password:** Tests that new password must be different
        6. **Valid password change:** Tests successful password change

        **Expected Results:**
        - Empty fields should show validation error
        - Password mismatch should show error
        - Wrong current password should show authentication error
        - Weak password should show complexity error
        - Same password should show error
        - Valid change should show success
        """)

    return app


def run_change_password_tests():
    """Run all change password tests and return results."""
    results = {}

    try:
        # Test interface creation
        test_change_password_interface()
        results["interface_creation"] = True
        print("✅ Change password interface created successfully")
    except Exception as e:
        results["interface_creation"] = False
        print(f"❌ Change password interface creation failed: {e}")

    try:
        # Test simple interface creation
        test_simple_change_password()
        results["simple_interface_creation"] = True
        print("✅ Simple change password interface created successfully")
    except Exception as e:
        results["simple_interface_creation"] = False
        print(f"❌ Simple change password interface creation failed: {e}")

    try:
        # Test validation interface creation
        test_change_password_validation()
        results["validation_interface_creation"] = True
        print("✅ Change password validation interface created successfully")
    except Exception as e:
        results["validation_interface_creation"] = False
        print(f"❌ Change password validation interface creation failed: {e}")

    try:
        # Test backend functionality
        import asyncio
        from backend import change_password_test
        from tests.test_utils import ensure_default_test_user, cleanup_test_user

        async def test_backend_functionality():
            # Ensure test user exists first
            user_created = ensure_default_test_user()
            print(f"[DEBUG] ensure_default_test_user() returned: {user_created}")
            if not user_created:
                print(
                    "❌ Failed to create test user for backend test. Aborting password change test."
                )
                return False

            # Removed get_user_by_username check because it does not exist in backend.py
            # After ensure_default_test_user(), proceed directly to password change test

            try:
                # Test successful password change
                result = await change_password_test(
                    "test_user", "TestPass123!", "NewPass456!"
                )
                if result.get("code") == "200":
                    print("✅ Backend change password functionality works")
                    # Change it back for future tests
                    reset_result = await change_password_test(
                        "test_user", "NewPass456!", "TestPass123!"
                    )
                    if reset_result.get("code") == "200":
                        print("✅ Password reset to original for future tests")
                        return True
                    else:
                        print(f"⚠️ Password reset failed: {reset_result}")
                        return False
                else:
                    print(f"⚠️ Backend change password returned: {result}")
                    return False
            finally:
                # Clean up test user
                cleanup_test_user("test_user")

        backend_success = asyncio.run(test_backend_functionality())
        results["backend_functionality"] = backend_success
    except Exception as e:
        results["backend_functionality"] = False
        print(f"❌ Backend functionality test failed: {e}")

    return results


if __name__ == "__main__":
    # Choose which test to run
    import sys

    if len(sys.argv) > 1:
        test_type = sys.argv[1]
    else:
        test_type = "simple"

    if test_type == "interface":
        app = test_change_password_interface()
    elif test_type == "validation":
        app = test_change_password_validation()
    elif test_type == "all":
        # Run all tests without launching
        results = run_change_password_tests()
        print("\n📊 Change Password Test Results:")
        for test_name, success in results.items():
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"  {test_name}: {status}")
        sys.exit(0 if all(results.values()) else 1)
    else:
        app = test_simple_change_password()

    # Use Docker-compatible launch configuration
    launch_config = {
        "debug": True,
        "share": False,
        "inbrowser": False,
        "quiet": False,
        "show_error": True,
        "server_name": "0.0.0.0",  # Listen on all interfaces for Docker
        "server_port": 7860,  # Use the same port as main app
    }

    print(
        f"🌐 Launching change password test app ({test_type}) on {launch_config['server_name']}:{launch_config['server_port']}"
    )
    print("Available test types: simple, interface, validation, all")
    app.launch(**launch_config)
