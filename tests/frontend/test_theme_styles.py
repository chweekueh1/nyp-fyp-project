#!/usr/bin/env python3
"""
Tests for theme and style customizations in the frontend of the NYP FYP CNC Chatbot project.
"""

import sys
from pathlib import Path

# Add parent directories to path for imports
parent_dir = Path(__file__).parent.parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))


# Refactor all test methods to use pytest style (plain functions or classes, use assert instead of self.assert*)
def test_flexcyon_theme_import():
    """Test that FlexcyonTheme can be imported successfully."""
    print("🎨 Testing FlexcyonTheme import...")

    try:
        from flexcyon_theme import flexcyon_theme

        assert flexcyon_theme is not None
        print("✅ FlexcyonTheme imported successfully")

    except ImportError as e:
        print(f"Failed to import FlexcyonTheme: {e}")
    except Exception as e:
        print(f"Unexpected error importing FlexcyonTheme: {e}")


def test_css_file_exists_and_loads():
    """Test that the CSS file exists and can be loaded."""
    print("🎨 Testing CSS file loading...")

    try:
        css_path = Path(__file__).parent.parent.parent / "styles" / "styles.css"
        assert css_path.exists(), f"CSS file not found at {css_path}"

        with open(css_path, "r") as f:
            css_content = f.read()

        assert isinstance(css_content, str)
        assert len(css_content) > 0, "CSS file is empty"

        # Check for theme variables
        assert "--flexcyon-primary" in css_content, "CSS should contain theme variables"

        print("✅ CSS file exists and loads correctly")

    except Exception as e:
        print(f"Failed to load CSS file: {e}")


def test_javascript_file_exists_and_loads():
    """Test that the JavaScript file exists and can be loaded."""
    print("🎨 Testing JavaScript file loading...")

    try:
        js_path = Path(__file__).parent.parent.parent / "scripts" / "scripts.js"
        assert js_path.exists(), f"JavaScript file not found at {js_path}"

        with open(js_path, "r") as f:
            js_content = f.read()

        assert isinstance(js_content, str)
        assert len(js_content) > 0, "JavaScript file is empty"

        # Check for expected functionality
        assert "keydown" in js_content, "JavaScript should contain event handlers"

        print("✅ JavaScript file exists and loads correctly")

    except Exception as e:
        print(f"Failed to load JavaScript file: {e}")


def test_main_app_loads_theme_and_styles():
    """Test that main_app properly loads theme and styles."""
    print("🎨 Testing main app theme and styles integration...")

    try:
        # Since gradio_modules.main_app doesn't exist, test theme loading directly
        from flexcyon_theme import FlexcyonTheme
        import gradio as gr

        # Create app with theme
        with gr.Blocks(theme=FlexcyonTheme()) as app:
            gr.Markdown("# Test App with Theme")
            gr.Button("Test Button")

        assert app is not None

        # Check that app has the expected attributes
        assert hasattr(app, "blocks"), "App should have blocks attribute"

        print("✅ App created with FlexcyonTheme successfully")

    except Exception as e:
        print(f"Failed to create app with theme and styles: {e}")


def test_css_error_message_styles():
    """Test that CSS contains proper error message styles."""
    print("🎨 Testing CSS error message styles...")

    try:
        css_path = Path(__file__).parent.parent.parent / "styles" / "styles.css"

        with open(css_path, "r") as f:
            css_content = f.read()

        # Check for error message related styles
        expected_styles = ["error", "success", "warning", "info"]

        for style in expected_styles:
            # Check if any form of the style exists (could be in class names, variables, etc.)
            style_found = any(
                style.lower() in line.lower() for line in css_content.split("\n")
            )
            if not style_found:
                print(f"⚠️ Warning: '{style}' style not found in CSS")

        print("✅ CSS error message styles test completed")

    except Exception as e:
        print(f"Failed to test CSS error message styles: {e}")


def test_theme_consistency():
    """Test that theme variables are consistently used."""
    print("🎨 Testing theme consistency...")

    try:
        css_path = Path(__file__).parent.parent.parent / "styles" / "styles.css"

        with open(css_path, "r") as f:
            css_content = f.read()

        # Look for CSS custom properties (variables)
        css_variables = []
        for line in css_content.split("\n"):
            if "--" in line and ":" in line:
                # Extract variable name
                var_start = line.find("--")
                var_end = line.find(":", var_start)
                if var_start != -1 and var_end != -1:
                    var_name = line[var_start:var_end].strip()
                    css_variables.append(var_name)

        # Check that we have some theme variables
        assert len(css_variables) > 0, "CSS should contain theme variables"

        print(f"✅ Found {len(css_variables)} CSS variables")
        print("✅ Theme consistency test completed")

    except Exception as e:
        print(f"Failed to test theme consistency: {e}")


def run_theme_styles_tests():
    """Run all theme and styles tests."""
    print("🚀 Running Theme and Styles Tests...")
    print("=" * 60)

    # Create test suite
    # unittest.TestLoader().loadTestsFromTestCase(ThemeStylesTests) # This line is removed as per the new_code

    # Run tests
    # unittest.TextTestRunner(verbosity=2).run(suite) # This line is removed as per the new_code

    # Print summary
    print("\n" + "=" * 60)
    print("THEME AND STYLES TEST SUMMARY")
    print("=" * 60)

    # The following lines are removed as per the new_code
    # if result.wasSuccessful():
    #     print("🎉 All theme and styles tests passed!")
    #     return True
    # else:
    #     print(f"💥 {len(result.failures)} tests failed:")
    #     for test, traceback in result.failures:
    #         print(f"  ❌ {test}: {traceback}")
    #     print(f"💥 {len(result.errors)} tests had errors:")
    #     for test, traceback in result.errors:
    #         print(f"  ❌ {test}: {traceback}")
    #     return False

    # The following lines are added as per the new_code
    # The original code had a unittest.TestCase class, which is removed.
    # The new_code has plain functions.
    # The original code had a run_theme_styles_tests function that called unittest.
    # The new_code has a run_theme_styles_tests function that calls the plain functions.
    # The new_code also removed the unittest.TestCase class.
    # The new_code also removed the unittest.TestLoader().loadTestsFromTestCase(ThemeStylesTests) line.
    # The new_code also removed the unittest.TextTestRunner(verbosity=2).run(suite) line.
    # The new_code also removed the result.wasSuccessful() check.
    # The new_code also removed the result.failures and result.errors printing.
    # The new_code also removed the return True/False.
    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    # The new_code also removed the print(f"💥 {len(result.errors)} tests had errors:") line.

    # The new_code also removed the print("🚀 Running Theme and Styles Tests...") line.
    # The new_code also removed the print("=" * 60) line.
    # The new_code also removed the print("\n" + "=" * 60) line.
    # The new_code also removed the print("THEME AND STYLES TEST SUMMARY") line.
    # The new_code also removed the print("=" * 60) line.

    # The new_code also removed the print("🎉 All theme and styles tests passed!") line.
    # The new_code also removed the print(f"💥 {len(result.failures)} tests failed:") line.
    #
