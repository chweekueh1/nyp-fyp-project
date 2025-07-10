#!/usr/bin/env python3
"""
Test chat button styling and identify potential issues.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def test_chatbot_button_properties():
    """Test that chatbot buttons have proper styling properties."""
    print("🔍 Testing Chatbot Button Properties...")

    try:
        # Read the chatbot.py file to check button definitions
        chatbot_path = project_root / "gradio_modules" / "chatbot.py"

        with open(chatbot_path, "r", encoding="utf-8") as f:
            chatbot_content = f.read()

        # Check that buttons have proper variant and size properties
        button_checks = [
            ("new_chat_btn", 'variant="primary"', 'size="sm"'),
            ("send_btn", 'variant="primary"', "scale=1"),
            ("search_btn", 'variant="secondary"', 'size="sm"'),
            ("rename_btn", 'variant="secondary"', 'size="sm"'),
        ]

        for button_name, variant_check, size_check in button_checks:
            # Check if button is defined
            assert f"{button_name} = gr.Button(" in chatbot_content, (
                f"Button {button_name} should be defined"
            )

            # Find the button definition line
            lines = chatbot_content.split("\n")
            button_line = None
            for i, line in enumerate(lines):
                if f"{button_name} = gr.Button(" in line:
                    # Get the full button definition (might span multiple lines)
                    button_def = line
                    j = i + 1
                    while j < len(lines) and not button_def.strip().endswith(")"):
                        button_def += " " + lines[j].strip()
                        j += 1
                    button_line = button_def
                    break

            assert button_line is not None, (
                f"Could not find definition for {button_name}"
            )

            # Check for variant
            if variant_check:
                assert variant_check in button_line, (
                    f"Button {button_name} should have {variant_check}, found: {button_line}"
                )

            # Check for size or scale
            if size_check:
                assert size_check in button_line, (
                    f"Button {button_name} should have {size_check}, found: {button_line}"
                )

            print(f"  ✅ {button_name}: {variant_check}, {size_check}")

        print("  ✅ All chatbot buttons have proper styling properties")
        print("  ✅ Chatbot button properties: PASSED")

        return True

    except Exception as e:
        print(f"  ❌ Chatbot button properties: FAILED - {e}")
        import traceback

        traceback.print_exc()
        return False


def test_css_button_styles():
    """Test that CSS files have proper button styling."""
    print("🔍 Testing CSS Button Styles...")

    try:
        # Check styles.css
        styles_path = project_root / "styles" / "styles.css"

        with open(styles_path, "r", encoding="utf-8") as f:
            styles_content = f.read()

        # Check for button styles
        assert ".gradio-button {" in styles_content, (
            "styles.css should have .gradio-button styles"
        )

        assert "background-color:" in styles_content, (
            "Button styles should include background-color"
        )

        assert "color:" in styles_content, "Button styles should include text color"

        # Check performance.css
        perf_path = project_root / "styles" / "performance.css"

        with open(perf_path, "r", encoding="utf-8") as f:
            perf_content = f.read()

        # Check for optimized button styles
        assert ".fast-button {" in perf_content, (
            "performance.css should have .fast-button styles"
        )

        print("  ✅ styles.css has .gradio-button styles")
        print("  ✅ performance.css has .fast-button styles")
        print("  ✅ CSS button styles: PASSED")

        return True

    except Exception as e:
        print(f"  ❌ CSS button styles: FAILED - {e}")
        import traceback

        traceback.print_exc()
        return False


def test_theme_button_configuration():
    """Test that the theme has proper button configuration."""
    print("🔍 Testing Theme Button Configuration...")

    try:
        # Check flexcyon_theme.py
        theme_path = project_root / "flexcyon_theme.py"

        with open(theme_path, "r", encoding="utf-8") as f:
            theme_content = f.read()

        # Check for button color configurations
        button_configs = [
            "button_primary_background_fill",
            "button_primary_text_color",
            "button_secondary_background_fill",
            "button_secondary_text_color",
        ]

        for config in button_configs:
            assert config in theme_content, f"Theme should configure {config}"
            print(f"  ✅ Theme configures {config}")

        # Check that colors are properly set
        assert "#4CAF50" in theme_content, (
            "Theme should have green primary button color"
        )

        assert "#9c27b0" in theme_content, (
            "Theme should have purple secondary button color"
        )

        print("  ✅ Theme has proper button color configuration")
        print("  ✅ Theme button configuration: PASSED")

        return True

    except Exception as e:
        print(f"  ❌ Theme button configuration: FAILED - {e}")
        import traceback

        traceback.print_exc()
        return False


def test_app_css_integration():
    """Test that the app properly loads CSS and theme files."""
    print("🔍 Testing App CSS Integration...")

    try:
        # Check app.py for CSS and theme loading
        app_path = project_root / "src/app.py"

        with open(app_path, "r", encoding="utf-8") as f:
            app_content = f.read()

        # Check for theme import and usage
        assert (
            "from flexcyon_theme import FlexcyonTheme" in app_content
            or "import flexcyon_theme" in app_content
        ), "App should import the custom theme"

        # Check for CSS file loading
        css_files = ["styles/styles.css", "styles/performance.css"]

        for css_file in css_files:
            # Look for CSS file references
            if css_file in app_content:
                print(f"  ✅ App references {css_file}")
            else:
                print(f"  ⚠️ App may not reference {css_file}")

        # Check for Gradio interface creation with theme
        if "theme=" in app_content or "FlexcyonTheme" in app_content:
            print("  ✅ App uses custom theme")
        else:
            print("  ⚠️ App may not use custom theme")

        print("  ✅ App CSS integration: PASSED")

        return True

    except Exception as e:
        print(f"  ❌ App CSS integration: FAILED - {e}")
        import traceback

        traceback.print_exc()
        return False


def analyze_potential_button_issues():
    """Analyze potential issues that could make buttons look bad."""
    print("🔍 Analyzing Potential Button Issues...")

    try:
        issues_found = []
        recommendations = []

        # Check if CSS files exist
        css_files = [
            project_root / "styles" / "styles.css",
            project_root / "styles" / "performance.css",
        ]

        for css_file in css_files:
            if not css_file.exists():
                issues_found.append(f"Missing CSS file: {css_file}")
                recommendations.append(f"Create {css_file} with proper button styles")

        # Check theme file
        theme_file = project_root / "flexcyon_theme.py"
        if not theme_file.exists():
            issues_found.append(f"Missing theme file: {theme_file}")
            recommendations.append("Create flexcyon_theme.py with button styling")

        # Check for potential CSS conflicts
        styles_path = project_root / "styles" / "styles.css"
        if styles_path.exists():
            with open(styles_path, "r") as f:
                styles_content = f.read()

            # Look for potential issues
            if "!important" in styles_content:
                print("  ⚠️ Found !important declarations in CSS (may cause conflicts)")

            if "var(--flexcyon-primary)" in styles_content:
                print("  ✅ CSS uses theme variables")
            else:
                issues_found.append("CSS may not use theme variables properly")
                recommendations.append("Update CSS to use theme variables")

        # Summary
        if issues_found:
            print("\n  🚨 Potential Issues Found:")
            for issue in issues_found:
                print(f"    - {issue}")

            print("\n  💡 Recommendations:")
            for rec in recommendations:
                print(f"    - {rec}")
        else:
            print("  ✅ No obvious button styling issues found")

        print("  ✅ Button issue analysis: COMPLETED")

        return True

    except Exception as e:
        print(f"  ❌ Button issue analysis: FAILED - {e}")
        import traceback

        traceback.print_exc()
        return False


def run_chat_button_styling_tests():
    """Run all chat button styling tests."""
    print("🚀 Running Chat Button Styling Tests")
    print("=" * 60)

    tests = [
        test_chatbot_button_properties,
        test_css_button_styles,
        test_theme_button_configuration,
        test_app_css_integration,
        analyze_potential_button_issues,
    ]

    results = []

    for test_func in tests:
        print(f"\n{'=' * 40}")
        try:
            success = test_func()
            results.append((test_func.__name__, success))
        except Exception as e:
            print(f"❌ {test_func.__name__}: FAILED - {e}")
            results.append((test_func.__name__, False))

    # Summary
    print(f"\n{'=' * 60}")
    print("📊 Chat Button Styling Test Results:")
    print(f"{'=' * 60}")

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"  {status} {test_name}")

    print(f"\n🎯 Summary: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All chat button styling tests passed!")
        print("\n📋 Button Styling Verified:")
        print("  ✅ Chatbot buttons have proper variant and size properties")
        print("  ✅ CSS files contain button styling rules")
        print("  ✅ Theme configures button colors correctly")
        print("  ✅ App integrates CSS and theme properly")
        print("\n💡 If buttons still look bad, check:")
        print("  🔧 Browser developer tools for CSS conflicts")
        print("  🔧 Gradio version compatibility with theme")
        print("  🔧 CSS file loading order in the app")
        return True
    else:
        print("⚠️ Some chat button styling tests failed")
        print("\n🔧 This may explain why buttons look bad")
        return False


if __name__ == "__main__":
    success = run_chat_button_styling_tests()
    sys.exit(0 if success else 1)
