import gradio as gr
import sys
import asyncio
from pathlib import Path

# Add parent directory to path for imports
parent_dir = Path(__file__).parent.parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Import backend functions directly
from backend import do_login, do_register

def test_login_interface():
    """Test the complete login interface with all features."""
    with gr.Blocks(title="Login Interface Test") as app:
        # Header
        gr.Markdown("# Login Interface Test")

        # Import and create login interface
        from gradio_modules.login_and_register import login_interface

        # Create login interface with default parameters
        login_interface(setup_events=True)
        
        # Status display
        gr.Markdown("## Test Instructions")
        gr.Markdown("""
        **Test the following:**
        1. **Login Button:** Try logging in with username: `test` and password: `test`
        2. **Register Button:** Click to switch to registration mode
        3. **Password Visibility:** Click the eye icon to toggle password visibility
        4. **Back to Login:** Click to switch back to login mode
        5. **Registration:** Try registering with valid credentials
        
        **Expected Behavior:**
        - Login button should respond and show success/error messages
        - Register button should switch the interface to registration mode
        - Password visibility toggle should work
        - All buttons should be clickable and responsive
        - Registration should validate password complexity
        """)
    
    return app

def test_simple_login():
    """Test a simplified login interface for basic functionality."""
    
    async def handle_login(username, password):
        """Handle login using backend function directly."""
        print(f"Login attempt: {username}, {password}")
        try:
            # Call backend function directly
            result = await do_login(username, password)
            print(f"Backend login result: {result}")
            
            if result.get('code') == '200':
                return f"✅ Login successful! Welcome, {username}!"
            else:
                return f"❌ Login failed: {result.get('message', 'Unknown error')}"
        except Exception as e:
            print(f"Login error: {e}")
            return f"❌ Login error: {str(e)}"
    
    async def handle_register(username, password, confirm_password):
        """Handle registration using backend function directly."""
        print(f"Register attempt: {username}, {password}, {confirm_password}")
        try:
            if password != confirm_password:
                return "❌ Passwords do not match!"
            
            # Call backend function directly
            result = await do_register(username, password)
            print(f"Backend register result: {result}")
            
            if result.get('code') == '200':
                return "✅ Registration successful! Please log in."
            else:
                return f"❌ Registration failed: {result.get('message', 'Unknown error')}"
        except Exception as e:
            print(f"Registration error: {e}")
            return f"❌ Registration error: {str(e)}"
    
    def toggle_password_visibility(current_visible):
        print(f"Toggle password visibility: {current_visible}")
        return not current_visible, "text" if not current_visible else "password"
    
    with gr.Blocks(title="Simple Login Test") as app:
        gr.Markdown("# Simple Login Test")
        
        # States
        password_visible = gr.State(False)
        username = gr.Textbox(label="Username", placeholder="Enter username", value="test")
        password = gr.Textbox(label="Password", placeholder="Enter password", type="password")
        confirm_password = gr.Textbox(label="Confirm Password", placeholder="Confirm password", type="password", visible=False)
        
        # Buttons
        with gr.Row():
            login_btn = gr.Button("Login", variant="primary")
            register_btn = gr.Button("Register", variant="secondary")
            toggle_btn = gr.Button("👁️ Toggle Password")
        
        # Output
        result = gr.Markdown("Enter credentials and click buttons to test...")
        
        # Event handlers
        login_btn.click(
            fn=handle_login,
            inputs=[username, password],
            outputs=[result],
            api_name="simple_login"
        )
        
        register_btn.click(
            fn=handle_register,
            inputs=[username, password, confirm_password],
            outputs=[result],
            api_name="simple_register"
        )
        
        toggle_btn.click(
            fn=toggle_password_visibility,
            inputs=[password_visible],
            outputs=[password_visible, password],
            api_name="toggle_password"
        )
        
        # Instructions
        gr.Markdown("""
        **Test Instructions:**
        1. Enter username: `test` and password: `test`
        2. Click **Login** - should show success message
        3. Click **Toggle Password** - should show/hide password
        4. Enter different passwords in password and confirm password
        5. Click **Register** - should show password mismatch error
        
        **Expected Behavior:**
        - All buttons should be clickable
        - Login should work with test/test credentials
        - Password toggle should work
        - Register should validate password matching
        - Backend functions should be called directly
        """)
    
    return app

if __name__ == "__main__":
    print("Creating login interface test...")
    app = test_login_interface()
    print("Launching login interface test...")
    app.launch(debug=True, share=False)