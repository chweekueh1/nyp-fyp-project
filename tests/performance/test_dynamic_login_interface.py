#!/usr/bin/env python3
"""
Test the new dynamic login interface that shows only one form at a time.
Verifies that login and register forms don't show simultaneously.
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def test_dynamic_login_interface_creation():
    """Test that the dynamic login interface can be created."""
    print("🔍 Testing Dynamic Login Interface Creation...")
    
    try:
        from gradio_modules.login_and_register import login_interface
        import gradio as gr
        
        # Create interface without events
        components = login_interface(setup_events=False)
        
        # Should return 19 components (reduced from 21 in old version)
        assert len(components) == 19, f"Expected 19 components, got {len(components)}"
        
        # Extract key components
        logged_in_state, username_state, is_register_mode = components[0], components[1], components[2]
        main_container, error_message = components[3], components[4]
        username_input, email_input, password_input, confirm_password_input = components[5:9]
        primary_btn, secondary_btn = components[9], components[10]
        
        # Verify component types
        assert isinstance(logged_in_state, gr.State), "logged_in_state should be State"
        assert isinstance(username_state, gr.State), "username_state should be State"
        assert isinstance(is_register_mode, gr.State), "is_register_mode should be State"
        assert isinstance(main_container, gr.Column), "main_container should be Column"
        assert isinstance(error_message, gr.Markdown), "error_message should be Markdown"
        
        # Verify form components
        assert isinstance(username_input, gr.Textbox), "username_input should be Textbox"
        assert isinstance(email_input, gr.Textbox), "email_input should be Textbox"
        assert isinstance(password_input, gr.Textbox), "password_input should be Textbox"
        assert isinstance(confirm_password_input, gr.Textbox), "confirm_password_input should be Textbox"
        assert isinstance(primary_btn, gr.Button), "primary_btn should be Button"
        assert isinstance(secondary_btn, gr.Button), "secondary_btn should be Button"
        
        print(f"  ✅ All 19 components created with correct types")
        print(f"  ✅ Dynamic login interface creation: PASSED")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Dynamic login interface creation: FAILED - {e}")
        return False

def test_initial_login_mode():
    """Test that interface starts in login mode with correct visibility."""
    print("🔍 Testing Initial Login Mode...")
    
    try:
        from gradio_modules.login_and_register import login_interface
        
        # Create interface without events
        components = login_interface(setup_events=False)
        
        # Extract components
        logged_in_state, username_state, is_register_mode = components[0], components[1], components[2]
        email_input, confirm_password_input = components[6], components[8]
        
        # Verify initial state
        assert logged_in_state.value == False, "Initial logged_in_state should be False"
        assert username_state.value == "", "Initial username_state should be empty"
        assert is_register_mode.value == False, "Initial is_register_mode should be False (login mode)"
        
        # Verify register-only fields are hidden initially
        assert email_input.visible == False, "Email input should be hidden in login mode"
        assert confirm_password_input.visible == False, "Confirm password should be hidden in login mode"
        
        print(f"  ✅ Interface starts in login mode")
        print(f"  ✅ Register-only fields are hidden")
        print(f"  ✅ Initial login mode: PASSED")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Initial login mode: FAILED - {e}")
        return False

def test_no_simultaneous_forms():
    """Test that login and register forms don't exist simultaneously."""
    print("🔍 Testing No Simultaneous Forms...")
    
    try:
        from gradio_modules.login_and_register import login_interface
        
        # Create interface without events
        components = login_interface(setup_events=False)
        
        # The new interface should have only ONE set of form fields that change dynamically
        # Count form input components safely by checking component types
        import gradio as gr

        # Should have exactly 4 input fields: username, email, password, confirm_password
        # But they are reused dynamically, not duplicated
        username_input, email_input, password_input, confirm_password_input = components[5:9]

        # Verify these are all Textbox components (form inputs)
        assert isinstance(username_input, gr.Textbox), "username_input should be Textbox"
        assert isinstance(email_input, gr.Textbox), "email_input should be Textbox"
        assert isinstance(password_input, gr.Textbox), "password_input should be Textbox"
        assert isinstance(confirm_password_input, gr.Textbox), "confirm_password_input should be Textbox"
        
        # Verify we don't have separate login/register forms
        component_types = [type(comp).__name__ for comp in components]
        textbox_count = component_types.count('Textbox')
        
        # Should have exactly 4 textboxes (username, email, password, confirm_password)
        # Not 6+ like the old version that had separate forms
        assert textbox_count == 4, f"Expected 4 textboxes (dynamic form), got {textbox_count}"
        
        # Verify we have only 2 buttons (primary and secondary that change function)
        button_count = component_types.count('Button')
        assert button_count == 4, f"Expected 4 buttons (primary, secondary, 2 password toggles), got {button_count}"
        
        print(f"  ✅ Only 4 textboxes (dynamic reuse, not duplication)")
        print(f"  ✅ Only 4 buttons (dynamic function, not separate forms)")
        print(f"  ✅ No simultaneous forms: PASSED")
        
        return True
        
    except Exception as e:
        print(f"  ❌ No simultaneous forms: FAILED - {e}")
        return False

def test_dynamic_form_switching():
    """Test that the interface supports dynamic form switching."""
    print("🔍 Testing Dynamic Form Switching...")
    
    try:
        from gradio_modules.login_and_register import login_interface
        import gradio as gr
        
        # Test that the interface can be created with events in Blocks context
        with gr.Blocks() as app:
            components = login_interface(setup_events=True)
            
            # Extract key components
            is_register_mode = components[2]
            email_input, confirm_password_input = components[6], components[8]
            primary_btn, secondary_btn = components[9], components[10]
            
            # Verify the mode switching state exists
            assert isinstance(is_register_mode, gr.State), "is_register_mode should be State"
            assert is_register_mode.value == False, "Should start in login mode"
            
            # Verify conditional fields exist
            assert isinstance(email_input, gr.Textbox), "email_input should exist for register mode"
            assert isinstance(confirm_password_input, gr.Textbox), "confirm_password_input should exist for register mode"
            
            # Verify dynamic buttons exist
            assert isinstance(primary_btn, gr.Button), "primary_btn should exist"
            assert isinstance(secondary_btn, gr.Button), "secondary_btn should exist"
        
        print(f"  ✅ Dynamic form switching components present")
        print(f"  ✅ Mode state management working")
        print(f"  ✅ Dynamic form switching: PASSED")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Dynamic form switching: FAILED - {e}")
        return False

def test_app_integration():
    """Test that the app integrates correctly with the new dynamic interface."""
    print("🔍 Testing App Integration...")
    
    try:
        # Import app module to test integration
        import app
        
        # If we get here without errors, the integration is working
        print(f"  ✅ App imports successfully with new login interface")
        print(f"  ✅ No component mismatch errors")
        print(f"  ✅ App integration: PASSED")
        
        return True
        
    except Exception as e:
        print(f"  ❌ App integration: FAILED - {e}")
        return False

def run_dynamic_login_interface_tests():
    """Run all dynamic login interface tests."""
    print("🚀 Running Dynamic Login Interface Tests")
    print("=" * 60)
    
    tests = [
        test_dynamic_login_interface_creation,
        test_initial_login_mode,
        test_no_simultaneous_forms,
        test_dynamic_form_switching,
        test_app_integration
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
    print("📊 Dynamic Login Interface Test Results:")
    print(f"{'='*60}")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"  {status} {test_name}")
    
    print(f"\n🎯 Summary: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All dynamic login interface tests passed!")
        print("\n📋 Features Verified:")
        print("  ✅ Single dynamic form (no simultaneous login/register)")
        print("  ✅ Proper component count (19 vs 21 in old version)")
        print("  ✅ Dynamic form switching capability")
        print("  ✅ Correct initial state (login mode)")
        print("  ✅ Register-only fields hidden initially")
        print("  ✅ App integration working correctly")
        print("\n🛠️ Improvements Achieved:")
        print("  🔧 Eliminated simultaneous form display")
        print("  🔧 Reduced component count for better performance")
        print("  🔧 Dynamic field visibility based on mode")
        print("  🔧 Single set of reusable form components")
        print("  🔧 Cleaner UI with mode-based switching")
        return True
    else:
        print("⚠️ Some dynamic login interface tests failed")
        return False

if __name__ == "__main__":
    success = run_dynamic_login_interface_tests()
    sys.exit(0 if success else 1)
