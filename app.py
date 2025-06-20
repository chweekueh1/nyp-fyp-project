#!/usr/bin/env python3
"""
NYP FYP Chatbot Application - Clean Build
Building each interface step by step with thorough testing.
"""

import sys
import asyncio
from pathlib import Path
import gradio as gr
from utils import setup_logging

# Add parent directory to path for imports
parent_dir = Path(__file__).parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Set up logging
logger = setup_logging()

def initialize_backend():
    """Initialize the backend before loading interfaces."""
    logger.info("🚀 Initializing backend services...")

    try:
        # Import backend initialization
        from backend import init_backend

        # Initialize backend asynchronously
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            loop.run_until_complete(init_backend())
            logger.info("✅ Backend initialization completed successfully")
            return True
        finally:
            loop.close()

    except Exception as e:
        logger.error(f"❌ Backend initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_loading_app():
    """Create a loading screen while backend initializes."""

    with gr.Blocks(title="NYP FYP Chatbot - Loading") as app:
        with gr.Column(elem_id="loading_container"):
            gr.Markdown("# 🚀 NYP FYP Chatbot")
            gr.Markdown("## ⏳ Initializing Backend Services...")

            # Loading animation using HTML/CSS
            gr.HTML("""
            <div style="display: flex; justify-content: center; align-items: center; margin: 20px;">
                <div style="
                    border: 4px solid #f3f3f3;
                    border-top: 4px solid #3498db;
                    border-radius: 50%;
                    width: 50px;
                    height: 50px;
                    animation: spin 1s linear infinite;
                "></div>
            </div>
            <style>
                @keyframes spin {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
                }
            </style>
            """)

            gr.Markdown("""
            **Please wait while we:**
            - 🤖 Initialize AI models
            - 🗄️ Connect to databases
            - 🔐 Set up authentication
            - 📊 Load vector stores
            """)

            gr.Markdown("*This may take a few moments...*")

    return app

def create_app_with_login():
    """Create app with integrated login interface."""

    with gr.Blocks(title="NYP FYP Chatbot - With Login") as app:
        gr.Markdown("# 🚀 NYP FYP Chatbot")

        # State variables
        logged_in_state = gr.State(False)
        username_state = gr.State("")

        # Create main containers
        with gr.Column(visible=True) as login_container:
            gr.Markdown("## 🔐 Login")
            gr.Markdown("Please log in to access the chatbot.")

            username_input = gr.Textbox(
                label="Username or Email",
                placeholder="Enter your username or email",
                elem_id="username_input"
            )

            with gr.Row():
                password_input = gr.Textbox(
                    label="Password",
                    placeholder="Enter your password",
                    type="password",
                    elem_id="password_input",
                    scale=4
                )
                show_password_btn = gr.Button("👁️", elem_id="show_password_btn", scale=1, size="sm")

            with gr.Row():
                login_btn = gr.Button("Login", variant="primary", elem_id="login_btn")
                register_btn = gr.Button("Register", variant="secondary", elem_id="register_btn")

        with gr.Column(visible=False) as register_container:
            gr.Markdown("## 📝 Register")
            gr.Markdown("Create a new account to access the chatbot.")

            register_username = gr.Textbox(
                label="Username",
                placeholder="Choose a username (3-20 characters)",
                elem_id="register_username"
            )

            register_email = gr.Textbox(
                label="Email",
                placeholder="Enter your authorized email address",
                elem_id="register_email"
            )

            # Show allowed email domains
            gr.Markdown("""
            **Authorized Email Domains:**
            - @nyp.edu.sg (NYP staff/faculty)
            - @student.nyp.edu.sg (NYP students)
            - Selected test emails for development
            """, elem_id="allowed_emails_info")

            with gr.Row():
                register_password = gr.Textbox(
                    label="Password",
                    placeholder="Choose a strong password (min 8 characters)",
                    type="password",
                    elem_id="register_password",
                    scale=4
                )
                show_reg_password_btn = gr.Button("👁️", elem_id="show_reg_password_btn", scale=1, size="sm")

            with gr.Row():
                register_confirm = gr.Textbox(
                    label="Confirm Password",
                    placeholder="Confirm your password",
                    type="password",
                    elem_id="register_confirm",
                    scale=4
                )
                show_reg_confirm_btn = gr.Button("👁️", elem_id="show_reg_confirm_btn", scale=1, size="sm")

            # Password requirements
            gr.Markdown("""
            **Password Requirements:**
            - At least 8 characters long
            - Contains uppercase and lowercase letters
            - Contains at least one number
            - Contains at least one special character (!@#$%^&*)
            """)

            with gr.Row():
                register_submit_btn = gr.Button("Register Account", variant="primary", elem_id="register_submit_btn")
                back_to_login_btn = gr.Button("Back to Login", variant="secondary", elem_id="back_to_login_btn")

        with gr.Column(visible=False) as main_container:
            gr.Markdown("## 🎉 Welcome!")
            user_info = gr.Markdown("", elem_id="user_info")

            # Placeholder for other interfaces
            gr.Markdown("### 📋 Available Interfaces:")
            gr.Markdown("""
            - [x] 🔐 Login Interface ✅
            - [ ] 💬 Chat Interface (Coming Next)
            - [ ] 🔍 Search Interface
            - [ ] 📁 File Upload Interface
            - [ ] 🎤 Audio Interface
            - [ ] 🎨 Theme & Styling
            """)

            logout_btn = gr.Button("Logout", variant="secondary", elem_id="logout_btn")

        # Error/success messages
        error_message = gr.Markdown(visible=False, elem_id="error_message")

        # Login handler
        def handle_login(username, password):
            logger.info(f"Login attempt for user: {username}")

            # Input validation
            if not username or not username.strip():
                return False, "", gr.update(visible=True), gr.update(visible=False), gr.update(visible=False), gr.update(visible=True, value="❌ **Error:** Username is required"), ""
            if not password or not password.strip():
                return False, "", gr.update(visible=True), gr.update(visible=False), gr.update(visible=False), gr.update(visible=True, value="❌ **Error:** Password is required"), ""

            try:
                import asyncio
                from backend import do_login

                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(do_login(username.strip(), password))
                loop.close()

                if result.get("code") == "200":
                    actual_username = result.get("username", username.strip())
                    logger.info(f"Login successful for user: {actual_username}")
                    return True, actual_username, gr.update(visible=False), gr.update(visible=False), gr.update(visible=True), gr.update(visible=False), f"**Logged in as:** {actual_username}"
                else:
                    error_msg = result.get("message", "Login failed")
                    logger.warning(f"Login failed for user {username}: {error_msg}")
                    return False, "", gr.update(visible=True), gr.update(visible=False), gr.update(visible=False), gr.update(visible=True, value=f"❌ **Login failed:** {error_msg}"), ""
            except Exception as e:
                logger.error(f"Login error for user {username}: {e}")
                return False, "", gr.update(visible=True), gr.update(visible=False), gr.update(visible=False), gr.update(visible=True, value=f"❌ **System error:** {str(e)}"), ""

        # Register handler
        def handle_register(username, email, password, confirm):
            logger.info(f"Registration attempt for user: {username}")

            # Input validation
            if not username or not username.strip():
                return False, "", gr.update(visible=False), gr.update(visible=True), gr.update(visible=False), gr.update(visible=True, value="❌ **Error:** Username is required"), ""
            if not email or not email.strip():
                return False, "", gr.update(visible=False), gr.update(visible=True), gr.update(visible=False), gr.update(visible=True, value="❌ **Error:** Email is required"), ""
            if not password or not password.strip():
                return False, "", gr.update(visible=False), gr.update(visible=True), gr.update(visible=False), gr.update(visible=True, value="❌ **Error:** Password is required"), ""
            if not confirm or not confirm.strip():
                return False, "", gr.update(visible=False), gr.update(visible=True), gr.update(visible=False), gr.update(visible=True, value="❌ **Error:** Please confirm your password"), ""
            if password != confirm:
                return False, "", gr.update(visible=False), gr.update(visible=True), gr.update(visible=False), gr.update(visible=True, value="❌ **Error:** Passwords do not match"), ""

            try:
                import asyncio
                from backend import do_register

                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(do_register(username.strip(), password, email.strip()))
                loop.close()

                if result.get("code") == "200":
                    logger.info(f"Registration successful for user: {username}")
                    return False, "", gr.update(visible=True), gr.update(visible=False), gr.update(visible=False), gr.update(visible=True, value="✅ **Registration successful!** Please log in with your new account."), ""
                else:
                    error_msg = result.get("message", "Registration failed")
                    logger.warning(f"Registration failed for user {username}: {error_msg}")
                    return False, "", gr.update(visible=False), gr.update(visible=True), gr.update(visible=False), gr.update(visible=True, value=f"❌ **Registration failed:** {error_msg}"), ""
            except Exception as e:
                logger.error(f"Registration error for user {username}: {e}")
                return False, "", gr.update(visible=False), gr.update(visible=True), gr.update(visible=False), gr.update(visible=True, value=f"❌ **System error:** {str(e)}"), ""

        # Navigation handlers
        def switch_to_register():
            return gr.update(visible=False), gr.update(visible=True), gr.update(visible=False), gr.update(visible=False)

        def switch_to_login():
            return gr.update(visible=True), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False)

        def do_logout():
            logger.info("User logged out")
            return False, "", gr.update(visible=True), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), ""

        # Wire up events
        login_btn.click(
            fn=handle_login,
            inputs=[username_input, password_input],
            outputs=[logged_in_state, username_state, login_container, register_container, main_container, error_message, user_info]
        )

        register_btn.click(
            fn=switch_to_register,
            outputs=[login_container, register_container, main_container, error_message]
        )

        register_submit_btn.click(
            fn=handle_register,
            inputs=[register_username, register_email, register_password, register_confirm],
            outputs=[logged_in_state, username_state, login_container, register_container, main_container, error_message, user_info]
        )

        back_to_login_btn.click(
            fn=switch_to_login,
            outputs=[login_container, register_container, main_container, error_message]
        )

        logout_btn.click(
            fn=do_logout,
            outputs=[logged_in_state, username_state, login_container, register_container, main_container, error_message, user_info]
        )

        # Add Enter key support
        password_input.submit(
            fn=handle_login,
            inputs=[username_input, password_input],
            outputs=[logged_in_state, username_state, login_container, register_container, main_container, error_message, user_info]
        )

        register_confirm.submit(
            fn=handle_register,
            inputs=[register_username, register_email, register_password, register_confirm],
            outputs=[logged_in_state, username_state, login_container, register_container, main_container, error_message, user_info]
        )

    return app

def create_app_with_loading():
    """Create app that shows loading screen while backend initializes, then switches to login."""

    with gr.Blocks(title="NYP FYP Chatbot", css="""
        /* Password toggle button styling */
        #show_password_btn, #show_reg_password_btn, #show_reg_confirm_btn {
            min-width: 40px !important;
            padding: 8px !important;
            font-size: 16px !important;
            border-radius: 6px !important;
            background: #f8f9fa !important;
            border: 1px solid #dee2e6 !important;
            cursor: pointer !important;
        }

        #show_password_btn:hover, #show_reg_password_btn:hover, #show_reg_confirm_btn:hover {
            background: #e9ecef !important;
            border-color: #adb5bd !important;
        }

        /* Loading animation styling */
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        /* Improve form layout */
        .gradio-container {
            max-width: 500px !important;
            margin: 0 auto !important;
        }
    """) as app:
        # State to track initialization
        backend_ready = gr.State(False)

        # Loading screen container
        with gr.Column(visible=True, elem_id="loading_container") as loading_screen:
            gr.Markdown("# 🚀 NYP FYP Chatbot")
            gr.Markdown("## ⏳ Initializing Backend Services...")

            # Loading animation
            gr.HTML("""
            <div style="display: flex; justify-content: center; align-items: center; margin: 30px;">
                <div style="
                    border: 6px solid #f3f3f3;
                    border-top: 6px solid #3498db;
                    border-radius: 50%;
                    width: 60px;
                    height: 60px;
                    animation: spin 1s linear infinite;
                "></div>
            </div>
            <style>
                @keyframes spin {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
                }
            </style>
            """)

            # Status updates
            status_text = gr.Markdown("🔧 **Starting backend initialization...**")

            gr.Markdown("""
            **Please wait while we:**
            - 🤖 Initialize AI models
            - 🗄️ Connect to databases
            - 🔐 Set up authentication
            - 📊 Load vector stores
            - 🎨 Prepare user interface

            *This may take a few moments on first startup...*
            """)

        # Main login interface (hidden initially)
        with gr.Column(visible=False, elem_id="main_interface") as main_interface:
            # State variables for login
            logged_in_state = gr.State(False)
            username_state = gr.State("")

            # State variables for password visibility
            login_password_visible = gr.State(False)
            register_password_visible = gr.State(False)
            register_confirm_visible = gr.State(False)

            # Login container
            with gr.Column(visible=True) as login_container:
                gr.Markdown("# 🚀 NYP FYP Chatbot")
                gr.Markdown("## 🔐 Login")
                gr.Markdown("Please log in to access the chatbot.")

                username_input = gr.Textbox(
                    label="Username or Email",
                    placeholder="Enter your username or email",
                    elem_id="username_input"
                )

                with gr.Row():
                    password_input = gr.Textbox(
                        label="Password",
                        placeholder="Enter your password",
                        type="password",
                        elem_id="password_input",
                        scale=4
                    )
                    show_password_btn = gr.Button("👁️", elem_id="show_password_btn", scale=1, size="sm")

                with gr.Row():
                    login_btn = gr.Button("Login", variant="primary", elem_id="login_btn")
                    register_btn = gr.Button("Register", variant="secondary", elem_id="register_btn")

            # Register container
            with gr.Column(visible=False) as register_container:
                gr.Markdown("## 📝 Register")
                gr.Markdown("Create a new account to access the chatbot.")

                register_username = gr.Textbox(
                    label="Username",
                    placeholder="Choose a username (3-20 characters)",
                    elem_id="register_username"
                )

                register_email = gr.Textbox(
                    label="Email",
                    placeholder="Enter your authorized email address",
                    elem_id="register_email"
                )

                # Show allowed email domains
                gr.Markdown("""
                **Authorized Email Domains:**
                - @nyp.edu.sg (NYP staff/faculty)
                - @student.nyp.edu.sg (NYP students)
                - Selected test emails for development
                """, elem_id="allowed_emails_info")

                with gr.Row():
                    register_password = gr.Textbox(
                        label="Password",
                        placeholder="Choose a strong password (min 8 characters)",
                        type="password",
                        elem_id="register_password",
                        scale=4
                    )
                    show_reg_password_btn = gr.Button("👁️", elem_id="show_reg_password_btn", scale=1, size="sm")

                with gr.Row():
                    register_confirm = gr.Textbox(
                        label="Confirm Password",
                        placeholder="Confirm your password",
                        type="password",
                        elem_id="register_confirm",
                        scale=4
                    )
                    show_reg_confirm_btn = gr.Button("👁️", elem_id="show_reg_confirm_btn", scale=1, size="sm")

                # Password requirements
                gr.Markdown("""
                **Password Requirements:**
                - At least 8 characters long
                - Contains uppercase and lowercase letters
                - Contains at least one number
                - Contains at least one special character (!@#$%^&*)
                """)

                with gr.Row():
                    register_submit_btn = gr.Button("Register Account", variant="primary", elem_id="register_submit_btn")
                    back_to_login_btn = gr.Button("Back to Login", variant="secondary", elem_id="back_to_login_btn")

            # Main app container (after login)
            with gr.Column(visible=False) as main_container:
                gr.Markdown("## 🎉 Welcome!")
                user_info = gr.Markdown("", elem_id="user_info")

                # Enhanced Chatbot Interface
                gr.Markdown("### 💬 Enhanced Chatbot")

                # Import the enhanced chatbot UI
                try:
                    from gradio_modules.chatbot import chatbot_ui

                    # Create states for the enhanced chatbot interface
                    chat_history_state = gr.State([])
                    selected_chat_id = gr.State("")

                    # Create the enhanced chatbot interface
                    chat_selector, new_chat_btn, chatbot, msg, send_btn, chat_debug = chatbot_ui(
                        username_state, chat_history_state, selected_chat_id, setup_events=True
                    )

                    # Debug info will be displayed automatically as part of the chatbot interface

                except ImportError as e:
                    gr.Markdown(f"⚠️ **Chatbot interface not available:** {e}")
                    gr.Markdown("Using basic text interface as fallback.")

                    # Fallback basic interface
                    basic_chat_input = gr.Textbox(label="Message", placeholder="Type your message here...")
                    basic_send_btn = gr.Button("Send", variant="primary")
                    basic_output = gr.Textbox(label="Response", interactive=False)

                logout_btn = gr.Button("Logout", variant="secondary", elem_id="logout_btn")

            # Error/success messages
            error_message = gr.Markdown(visible=False, elem_id="error_message")

        # Backend initialization function
        def initialize_backend_async():
            """Initialize backend and update UI accordingly."""
            try:
                logger.info("🔧 Starting backend initialization...")
                yield gr.update(value="🔧 **Initializing AI models...**"), gr.update(visible=True), gr.update(visible=False), False

                # Initialize backend
                success = initialize_backend()

                if success:
                    logger.info("✅ Backend initialization completed")
                    yield gr.update(value="✅ **Backend ready! Loading interface...**"), gr.update(visible=False), gr.update(visible=True), True
                else:
                    logger.error("❌ Backend initialization failed")
                    yield gr.update(value="❌ **Backend initialization failed!**"), gr.update(visible=True), gr.update(visible=False), False

            except Exception as e:
                logger.error(f"❌ Backend initialization error: {e}")
                yield gr.update(value=f"❌ **Error: {str(e)}**"), gr.update(visible=True), gr.update(visible=False), False

        # Login handler (same as before)
        def handle_login(username, password):
            logger.info(f"Login attempt for user: {username}")

            # Input validation
            if not username or not username.strip():
                return False, "", gr.update(visible=True), gr.update(visible=False), gr.update(visible=False), gr.update(visible=True, value="❌ **Error:** Username is required"), ""
            if not password or not password.strip():
                return False, "", gr.update(visible=True), gr.update(visible=False), gr.update(visible=False), gr.update(visible=True, value="❌ **Error:** Password is required"), ""

            try:
                import asyncio
                from backend import do_login

                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(do_login(username.strip(), password))
                loop.close()

                if result.get("code") == "200":
                    actual_username = result.get("username", username.strip())
                    logger.info(f"Login successful for user: {actual_username}")
                    return True, actual_username, gr.update(visible=False), gr.update(visible=False), gr.update(visible=True), gr.update(visible=False), f"**Logged in as:** {actual_username}"
                else:
                    error_msg = result.get("message", "Login failed")
                    logger.warning(f"Login failed for user {username}: {error_msg}")
                    return False, "", gr.update(visible=True), gr.update(visible=False), gr.update(visible=False), gr.update(visible=True, value=f"❌ **Login failed:** {error_msg}"), ""
            except Exception as e:
                logger.error(f"Login error for user {username}: {e}")
                return False, "", gr.update(visible=True), gr.update(visible=False), gr.update(visible=False), gr.update(visible=True, value=f"❌ **System error:** {str(e)}"), ""

        # Register handler (same as before)
        def handle_register(username, email, password, confirm):
            logger.info(f"Registration attempt for user: {username}")

            # Input validation
            if not username or not username.strip():
                return False, "", gr.update(visible=False), gr.update(visible=True), gr.update(visible=False), gr.update(visible=True, value="❌ **Error:** Username is required"), ""
            if not email or not email.strip():
                return False, "", gr.update(visible=False), gr.update(visible=True), gr.update(visible=False), gr.update(visible=True, value="❌ **Error:** Email is required"), ""
            if not password or not password.strip():
                return False, "", gr.update(visible=False), gr.update(visible=True), gr.update(visible=False), gr.update(visible=True, value="❌ **Error:** Password is required"), ""
            if not confirm or not confirm.strip():
                return False, "", gr.update(visible=False), gr.update(visible=True), gr.update(visible=False), gr.update(visible=True, value="❌ **Error:** Please confirm your password"), ""
            if password != confirm:
                return False, "", gr.update(visible=False), gr.update(visible=True), gr.update(visible=False), gr.update(visible=True, value="❌ **Error:** Passwords do not match"), ""

            try:
                import asyncio
                from backend import do_register

                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(do_register(username.strip(), password, email.strip()))
                loop.close()

                if result.get("code") == "200":
                    logger.info(f"Registration successful for user: {username}")
                    return False, "", gr.update(visible=True), gr.update(visible=False), gr.update(visible=False), gr.update(visible=True, value="✅ **Registration successful!** Please log in with your new account."), ""
                else:
                    error_msg = result.get("message", "Registration failed")
                    logger.warning(f"Registration failed for user {username}: {error_msg}")
                    return False, "", gr.update(visible=False), gr.update(visible=True), gr.update(visible=False), gr.update(visible=True, value=f"❌ **Registration failed:** {error_msg}"), ""
            except Exception as e:
                logger.error(f"Registration error for user {username}: {e}")
                return False, "", gr.update(visible=False), gr.update(visible=True), gr.update(visible=False), gr.update(visible=True, value=f"❌ **System error:** {str(e)}"), ""

        # Password toggle handlers
        def toggle_login_password(is_visible):
            """Toggle login password visibility."""
            if is_visible:
                return gr.update(type="password"), "👁️", False
            else:
                return gr.update(type="text"), "🙈", True

        def toggle_register_password(is_visible):
            """Toggle register password visibility."""
            if is_visible:
                return gr.update(type="password"), "👁️", False
            else:
                return gr.update(type="text"), "🙈", True

        def toggle_register_confirm(is_visible):
            """Toggle register confirm password visibility."""
            if is_visible:
                return gr.update(type="password"), "👁️", False
            else:
                return gr.update(type="text"), "🙈", True

        # Navigation handlers
        def switch_to_register():
            return gr.update(visible=False), gr.update(visible=True), gr.update(visible=False), gr.update(visible=False)

        def switch_to_login():
            return gr.update(visible=True), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False)

        def do_logout():
            logger.info("User logged out")
            return False, "", gr.update(visible=True), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), ""

        # Wire up password toggle events
        show_password_btn.click(
            fn=toggle_login_password,
            inputs=[login_password_visible],
            outputs=[password_input, show_password_btn, login_password_visible]
        )

        show_reg_password_btn.click(
            fn=toggle_register_password,
            inputs=[register_password_visible],
            outputs=[register_password, show_reg_password_btn, register_password_visible]
        )

        show_reg_confirm_btn.click(
            fn=toggle_register_confirm,
            inputs=[register_confirm_visible],
            outputs=[register_confirm, show_reg_confirm_btn, register_confirm_visible]
        )

        # Wire up events (only when backend is ready)
        login_btn.click(
            fn=handle_login,
            inputs=[username_input, password_input],
            outputs=[logged_in_state, username_state, login_container, register_container, main_container, error_message, user_info]
        )

        register_btn.click(
            fn=switch_to_register,
            outputs=[login_container, register_container, main_container, error_message]
        )

        register_submit_btn.click(
            fn=handle_register,
            inputs=[register_username, register_email, register_password, register_confirm],
            outputs=[logged_in_state, username_state, login_container, register_container, main_container, error_message, user_info]
        )

        back_to_login_btn.click(
            fn=switch_to_login,
            outputs=[login_container, register_container, main_container, error_message]
        )

        logout_btn.click(
            fn=do_logout,
            outputs=[logged_in_state, username_state, login_container, register_container, main_container, error_message, user_info]
        )

        # Add Enter key support
        password_input.submit(
            fn=handle_login,
            inputs=[username_input, password_input],
            outputs=[logged_in_state, username_state, login_container, register_container, main_container, error_message, user_info]
        )

        register_confirm.submit(
            fn=handle_register,
            inputs=[register_username, register_email, register_password, register_confirm],
            outputs=[logged_in_state, username_state, login_container, register_container, main_container, error_message, user_info]
        )

        # Auto-start initialization when app loads
        app.load(
            fn=initialize_backend_async,
            outputs=[status_text, loading_screen, main_interface, backend_ready]
        )

    return app

if __name__ == "__main__":
    print("🚀 Starting NYP FYP Chatbot with Non-Blocking Loading")
    print("=" * 60)
    print("🎨 Creating application with loading screen...")
    print("⏳ Backend will initialize after UI loads...")

    try:
        # Create app with non-blocking loading
        app = create_app_with_loading()
        print("✅ Application interface created successfully")
        print("🌐 Launching application...")
        print("=" * 60)
        print("🔄 Loading Features:")
        print("  - Non-blocking loading screen")
        print("  - Backend initializes after UI renders")
        print("  - Real-time status updates")
        print("  - Smooth user experience")
        print("=" * 60)
        print("🔐 Enhanced Features Available:")
        print("  - Username or email login")
        print("  - Authorized email domains only")
        print("  - Enhanced password requirements")
        print("  - Email validation against allowed list")
        print("  - Password visibility toggles")
        print("=" * 60)
        print("📧 Authorized Email Domains:")
        print("  - @nyp.edu.sg (NYP staff/faculty)")
        print("  - @student.nyp.edu.sg (NYP students)")
        print("  - Selected test emails for development")
        print("=" * 60)

        app.launch(debug=True, share=False)

    except Exception as e:
        logger.error(f"❌ Failed to create or launch application: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
