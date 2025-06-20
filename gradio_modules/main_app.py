# gradio_modules/main_app.py
import gradio as gr
import sys
from pathlib import Path
import os
import json

# Add parent directory to path for imports
parent_dir = Path(__file__).parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from backend import list_user_chat_ids, get_chat_history, ask_question, CHAT_SESSIONS_PATH, create_and_persist_new_chat

def load_all_chats(username):
    chat_ids = list_user_chat_ids(username)
    all_histories = {}
    for cid in chat_ids:
        try:
            hist = get_chat_history(cid, username)
            all_histories[cid] = [list(pair) for pair in hist] if hist else []
        except Exception as e:
            all_histories[cid] = [["[Error loading chat]", str(e)]]
    return all_histories

def create_new_chat_id():
    import uuid
    return str(uuid.uuid4())

def send_message_to_chat(message, chat_id, all_histories, username):
    if not message.strip():
        return "", all_histories, chat_id, [["", "Please enter a message."]]
    if not chat_id:
        chat_id = create_new_chat_id()
        all_histories[chat_id] = []
    try:
        import asyncio
        result = asyncio.run(ask_question(message, chat_id, username))
        if result.get("code") == "200":
            answer = result.get("response", "")
            if isinstance(answer, dict) and "answer" in answer:
                answer = answer["answer"]
            all_histories[chat_id].append([message, answer])
        else:
            all_histories[chat_id].append([message, f"Error: {result.get('error', 'Unknown error')}"])
    except Exception as e:
        all_histories[chat_id].append([message, f"Exception: {e}"])
    return "", all_histories, chat_id, all_histories[chat_id]

def fuzzy_find_chats(query, all_histories):
    from difflib import get_close_matches
    results = []
    for cid, history in all_histories.items():
        all_text = " ".join([msg[0] + " " + msg[1] for msg in history])
        if query.lower() in all_text.lower() or get_close_matches(query, [all_text], n=1, cutoff=0.6):
            results.append(f"Chat {cid}: {all_text[:100]}...")
    return "\n\n".join(results) if results else "No matching chats found."



def main_app():
    """Main application with tabbed interface and improved error handling."""

    # Import the custom theme
    try:
        from flexcyon_theme import flexcyon_theme
        theme = flexcyon_theme
    except ImportError:
        print("Warning: Could not import flexcyon_theme, using default theme")
        theme = None

    # Load custom CSS
    custom_css = ""
    try:
        css_path = Path(__file__).parent.parent / "styles" / "styles.css"
        if css_path.exists():
            with open(css_path, 'r') as f:
                custom_css = f.read()
            print(f"✅ Loaded custom CSS from {css_path}")
        else:
            print(f"⚠️ CSS file not found at {css_path}")
    except Exception as e:
        print(f"⚠️ Error loading CSS: {e}")

    # Add additional CSS for error messages if not in main CSS
    additional_css = """
    .error-message {
        background-color: rgba(255, 107, 107, 0.1) !important;
        border: 1px solid #FF6B6B !important;
        border-radius: 4px !important;
        padding: 10px !important;
        margin: 5px 0 !important;
        color: #FF6B6B !important;
    }
    .success-message {
        background-color: rgba(78, 205, 196, 0.1) !important;
        border: 1px solid #4ECDC4 !important;
        border-radius: 4px !important;
        padding: 10px !important;
        margin: 5px 0 !important;
        color: #4ECDC4 !important;
    }
    .info-message {
        background-color: rgba(255, 230, 109, 0.1) !important;
        border: 1px solid #FFE66D !important;
        border-radius: 4px !important;
        padding: 10px !important;
        margin: 5px 0 !important;
        color: #FFE66D !important;
    }
    """

    # Combine CSS
    final_css = custom_css + additional_css

    # Load JavaScript
    js_code = ""
    try:
        js_path = Path(__file__).parent.parent / "scripts" / "scripts.js"
        if js_path.exists():
            with open(js_path, 'r') as f:
                js_code = f.read()
            print(f"✅ Loaded custom JavaScript from {js_path}")
        else:
            print(f"⚠️ JavaScript file not found at {js_path}")
    except Exception as e:
        print(f"⚠️ Error loading JavaScript: {e}")

    with gr.Blocks(title="NYP FYP Chatbot", theme=theme, css=final_css, js=js_code) as app:

        # States
        logged_in_state = gr.State(False)
        username_state = gr.State("")
        all_histories = gr.State({})
        selected_chat_id = gr.State("")

        # --- Unified Layout ---
        with gr.Group():
            # Login container
            with gr.Column(visible=True, elem_id="login-container") as login_container:
                error_message = gr.Markdown(visible=False)
                # Create login interface components manually to handle register button
                username_input = gr.Textbox(label="Username", placeholder="Enter your username")
                password_input = gr.Textbox(label="Password", placeholder="Enter your password", type="password")
                login_btn = gr.Button("Login")
                register_btn = gr.Button("Register")

            # Register container
            with gr.Column(visible=False, elem_id="register-container") as register_container:
                register_error_message = gr.Markdown(visible=False)
                register_username = gr.Textbox(label="Username", placeholder="Choose a username")
                register_password = gr.Textbox(label="Password", placeholder="Choose a password", type="password")
                register_confirm = gr.Textbox(label="Confirm Password", placeholder="Confirm password", type="password")
                register_submit_btn = gr.Button("Register Account")
                back_to_login_btn = gr.Button("Back to Login")

            # Main app container with tabbed interface
            with gr.Column(visible=False, elem_id="main-container") as main_container:
                # Header with user info and logout
                with gr.Row():
                    user_info = gr.Markdown(visible=True)
                    logout_btn = gr.Button("Logout", variant="secondary")

                # Global chat selector and new chat button
                with gr.Row():
                    chat_selector = gr.Dropdown(choices=[], label="Select Chat", scale=3)
                    new_chat_btn = gr.Button("New Chat", variant="primary", scale=1)

                # Tabbed interface for different functionalities
                with gr.Tabs() as tabs:
                    # Chat Tab
                    with gr.TabItem("💬 Chat", id="chat_tab"):
                        chatbot = gr.Chatbot(label="Chat History", height=400)
                        with gr.Row():
                            msg = gr.Textbox(label="Message", placeholder="Type your message here...", scale=4)
                            send_btn = gr.Button("Send", variant="primary", scale=1)
                        chat_error = gr.Markdown(visible=False, elem_classes=["error-message"])

                    # File Upload Tab
                    with gr.TabItem("📁 File Upload", id="file_tab"):
                        gr.Markdown("### Upload and analyze files")
                        file_upload = gr.File(label="Choose a file to upload", file_types=["text", "pdf", "docx", "xlsx"])
                        file_send_btn = gr.Button("Upload and Process File", variant="primary")
                        file_status = gr.Markdown(visible=False)
                        file_chatbot = gr.Chatbot(label="File Analysis Chat", height=300)

                    # Audio Input Tab
                    with gr.TabItem("🎤 Audio", id="audio_tab"):
                        gr.Markdown("### Record and transcribe audio")
                        audio_input = gr.Audio(sources=["microphone"], type="filepath", label="Record your message")
                        audio_send_btn = gr.Button("Process Audio", variant="primary")
                        audio_status = gr.Markdown(visible=False)
                        audio_chatbot = gr.Chatbot(label="Audio Chat", height=300)

                    # Search Tab
                    with gr.TabItem("🔍 Search", id="search_tab"):
                        gr.Markdown("### Search through your chat history")
                        search_box = gr.Textbox(label="Search Query", placeholder="Enter keywords to search your chats...")
                        search_btn = gr.Button("Search", variant="primary")
                        search_results = gr.Markdown()

                    # Chat Management Tab
                    with gr.TabItem("⚙️ Manage", id="manage_tab"):
                        gr.Markdown("### Manage your chats")
                        with gr.Row():
                            rename_box = gr.Textbox(label="New Chat Name", placeholder="Enter new name for current chat")
                            rename_btn = gr.Button("Rename Chat", variant="secondary")
                        rename_status = gr.Markdown(visible=False)

                        gr.Markdown("### Export/Import")
                        export_btn = gr.Button("Export All Chats", variant="secondary")
                        export_status = gr.Markdown(visible=False)

        # Login/Register handlers with improved error messages
        def handle_login(username, password):
            # Input validation
            if not username or not username.strip():
                return False, "", gr.update(visible=True), gr.update(visible=False), gr.update(visible=True, value="❌ **Error:** Username is required"), gr.update(visible=False)
            if not password or not password.strip():
                return False, "", gr.update(visible=True), gr.update(visible=False), gr.update(visible=True, value="❌ **Error:** Password is required"), gr.update(visible=False)

            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                from backend import do_login
                result = loop.run_until_complete(do_login(username.strip(), password))
                if result.get("code") == "200":
                    return True, username.strip(), gr.update(visible=False), gr.update(visible=True), gr.update(visible=False, value=""), gr.update(visible=False)
                else:
                    error_msg = result.get("message", "Login failed")
                    if result.get("code") == "404":
                        error_msg = "❌ **User not found.** Please check your username or register a new account."
                    elif result.get("code") == "401":
                        error_msg = "❌ **Invalid password.** Please check your password and try again."
                    else:
                        error_msg = f"❌ **Login failed:** {error_msg}"
                    return False, "", gr.update(visible=True), gr.update(visible=False), gr.update(visible=True, value=error_msg), gr.update(visible=False)
            except Exception as e:
                return False, "", gr.update(visible=True), gr.update(visible=False), gr.update(visible=True, value=f"❌ **System error:** {str(e)}"), gr.update(visible=False)
            finally:
                loop.close()

        def handle_register(username, password, confirm):
            # Input validation
            if not username or not username.strip():
                return False, "", gr.update(visible=False), gr.update(visible=True), gr.update(visible=True, value="❌ **Error:** Username is required"), gr.update(visible=False)
            if not password or not password.strip():
                return False, "", gr.update(visible=False), gr.update(visible=True), gr.update(visible=True, value="❌ **Error:** Password is required"), gr.update(visible=False)
            if not confirm or not confirm.strip():
                return False, "", gr.update(visible=False), gr.update(visible=True), gr.update(visible=True, value="❌ **Error:** Please confirm your password"), gr.update(visible=False)
            if password != confirm:
                return False, "", gr.update(visible=False), gr.update(visible=True), gr.update(visible=True, value="❌ **Error:** Passwords do not match"), gr.update(visible=False)
            if len(password) < 6:
                return False, "", gr.update(visible=False), gr.update(visible=True), gr.update(visible=True, value="❌ **Error:** Password must be at least 6 characters long"), gr.update(visible=False)

            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                from backend import do_register
                result = loop.run_until_complete(do_register(username.strip(), password))
                if result.get("code") == "200":
                    return False, "", gr.update(visible=True), gr.update(visible=False), gr.update(visible=True, value="✅ **Registration successful!** Please log in with your new account."), gr.update(visible=False)
                else:
                    error_msg = result.get("message", "Registration failed")
                    if result.get("code") == "409":
                        error_msg = "❌ **Username already exists.** Please choose a different username."
                    else:
                        error_msg = f"❌ **Registration failed:** {error_msg}"
                    return False, "", gr.update(visible=False), gr.update(visible=True), gr.update(visible=True, value=error_msg), gr.update(visible=False)
            except Exception as e:
                return False, "", gr.update(visible=False), gr.update(visible=True), gr.update(visible=True, value=f"❌ **System error:** {str(e)}"), gr.update(visible=False)
            finally:
                loop.close()

        def switch_to_register():
            return gr.update(visible=False), gr.update(visible=True)

        def switch_to_login():
            return gr.update(visible=True), gr.update(visible=False)

        # Wire up login/register events
        login_btn.click(
            fn=handle_login,
            inputs=[username_input, password_input],
            outputs=[logged_in_state, username_state, login_container, main_container, error_message, register_container]
        )

        # Also allow login on Enter key in password field
        password_input.submit(
            fn=handle_login,
            inputs=[username_input, password_input],
            outputs=[logged_in_state, username_state, login_container, main_container, error_message, register_container]
        )

        register_btn.click(
            fn=switch_to_register,
            outputs=[login_container, register_container]
        )

        register_submit_btn.click(
            fn=handle_register,
            inputs=[register_username, register_password, register_confirm],
            outputs=[logged_in_state, username_state, login_container, register_container, register_error_message, main_container]
        )

        # Also allow register on Enter key in confirm password field
        register_confirm.submit(
            fn=handle_register,
            inputs=[register_username, register_password, register_confirm],
            outputs=[logged_in_state, username_state, login_container, register_container, register_error_message, main_container]
        )

        back_to_login_btn.click(
            fn=switch_to_login,
            outputs=[login_container, register_container]
        )

        # Show user info
        def update_user_info(username):
            if not username:
                return gr.update(visible=False)
            return gr.update(visible=True, value=f"Logged in as: {username}")
        username_state.change(fn=update_user_info, inputs=[username_state], outputs=[user_info])

        # Load chats after login
        def on_login(logged_in, username):
            if not logged_in or not username:
                return {}, "", gr.update(choices=[], value=None), []
            chats = load_all_chats(username)
            chat_ids = list(chats.keys())
            selected = chat_ids[0] if chat_ids else None
            # Ensure selected value is in choices or None
            dropdown_value = selected if selected in chat_ids else None
            return chats, selected or "", gr.update(choices=chat_ids, value=dropdown_value), chats[selected] if selected else []
        logged_in_state.change(
            fn=on_login,
            inputs=[logged_in_state, username_state],
            outputs=[all_histories, selected_chat_id, chat_selector, chatbot]
        )

        # New chat
        def start_new_chat(all_histories, username):
            if not username:
                return gr.update(), "", all_histories, []
            new_id = create_and_persist_new_chat(username)
            all_histories[new_id] = []
            chat_ids = list(all_histories.keys())
            return gr.update(choices=chat_ids, value=new_id), new_id, all_histories, []
        new_chat_btn.click(
            start_new_chat,
            inputs=[all_histories, username_state],
            outputs=[chat_selector, selected_chat_id, all_histories, chatbot]
        )

        # Switch chat
        def switch_chat(chat_id, all_histories):
            if not chat_id or chat_id not in all_histories:
                return "", []
            return chat_id, all_histories.get(chat_id, [])
        chat_selector.change(
            fn=switch_chat,
            inputs=[chat_selector, all_histories],
            outputs=[selected_chat_id, chatbot]
        )

        # Send message
        send_btn.click(
            fn=lambda msg, chat_id, all_histories, username: send_message_to_chat(msg, chat_id, all_histories, username),
            inputs=[msg, selected_chat_id, all_histories, username_state],
            outputs=[msg, all_histories, selected_chat_id, chatbot]
        )

        # File upload handler with improved error messages
        def handle_file_upload(file_obj, chat_id, all_histories, username):
            if not username:
                return gr.update(visible=True, value="❌ **Error:** Please log in first"), all_histories, []
            if not file_obj:
                return gr.update(visible=True, value="❌ **Error:** Please select a file to upload"), all_histories, []

            try:
                filename = getattr(file_obj, 'name', 'unknown_file')
                file_size = getattr(file_obj, 'size', 0)

                # File size validation (10MB limit)
                if file_size > 10 * 1024 * 1024:
                    return gr.update(visible=True, value="❌ **Error:** File size exceeds 10MB limit"), all_histories, []

                # Get or create chat
                if not chat_id:
                    chat_id = create_and_persist_new_chat(username)
                    all_histories[chat_id] = []

                # Add file upload message to chat
                file_message = f"📁 Uploaded file: {filename}"
                response_message = f"✅ **File uploaded successfully!**\n\n**File:** {filename}\n**Size:** {file_size:,} bytes\n\nI can help you analyze this file. What would you like to know about it?"
                all_histories[chat_id].append([file_message, response_message])

                return gr.update(visible=True, value="✅ **File uploaded successfully!** Check the chat for details."), all_histories, all_histories[chat_id]
            except Exception as e:
                return gr.update(visible=True, value=f"❌ **Upload failed:** {str(e)}"), all_histories, []

        file_send_btn.click(
            fn=handle_file_upload,
            inputs=[file_upload, selected_chat_id, all_histories, username_state],
            outputs=[file_status, all_histories, file_chatbot]
        )

        # Audio input handler with improved error messages
        def handle_audio_input(audio_file, chat_id, all_histories, username):
            if not username:
                return gr.update(visible=True, value="❌ **Error:** Please log in first"), all_histories, []
            if not audio_file:
                return gr.update(visible=True, value="❌ **Error:** Please record an audio message first"), all_histories, []

            try:
                # Get or create chat
                if not chat_id:
                    chat_id = create_and_persist_new_chat(username)
                    all_histories[chat_id] = []

                # Add audio message to chat
                audio_message = "🎤 Audio message recorded"
                response_message = "🎧 **Audio received!**\n\nI've received your audio message. Audio transcription will be implemented in a future update. For now, please type your message in the chat tab."
                all_histories[chat_id].append([audio_message, response_message])

                return gr.update(visible=True, value="✅ **Audio processed!** Check the chat for details."), all_histories, all_histories[chat_id]
            except Exception as e:
                return gr.update(visible=True, value=f"❌ **Audio processing failed:** {str(e)}"), all_histories, []

        audio_send_btn.click(
            fn=handle_audio_input,
            inputs=[audio_input, selected_chat_id, all_histories, username_state],
            outputs=[audio_status, all_histories, audio_chatbot]
        )

        # Search handler with improved functionality
        def handle_search(query, all_histories, username):
            if not username:
                return "❌ **Error:** Please log in first"
            if not query or not query.strip():
                return "❌ **Error:** Please enter a search query"

            try:
                from backend import fuzzy_search_chats
                results = fuzzy_search_chats(username, query.strip())
                if "No matching chats found" in results:
                    return f"🔍 **No results found** for '{query}'\n\nTry different keywords or check your spelling."
                else:
                    return f"🔍 **Search results for '{query}':**\n\n{results}"
            except Exception as e:
                return f"❌ **Search failed:** {str(e)}"

        search_btn.click(
            fn=handle_search,
            inputs=[search_box, all_histories, username_state],
            outputs=[search_results]
        )

        # Also allow search on Enter key
        search_box.submit(
            fn=handle_search,
            inputs=[search_box, all_histories, username_state],
            outputs=[search_results]
        )

        # Rename chat with proper file renaming and dropdown updates
        def handle_rename_chat(chat_id, new_name, all_histories, username):
            if not username:
                return all_histories, "❌ **Error:** Please log in first", chat_id, gr.update()
            if not chat_id:
                return all_histories, "❌ **Error:** No chat selected", chat_id, gr.update()
            if not new_name or not new_name.strip():
                return all_histories, "❌ **Error:** Please enter a new name", chat_id, gr.update()

            new_name = new_name.strip()
            if new_name == chat_id:
                return all_histories, "ℹ️ **Info:** Chat name is already '{}'".format(new_name), chat_id, gr.update()

            try:
                from backend import CHAT_SESSIONS_PATH
                import os

                # Check if new name already exists
                user_folder = os.path.join(CHAT_SESSIONS_PATH, username)
                old_path = os.path.join(user_folder, f"{chat_id}.json")
                new_path = os.path.join(user_folder, f"{new_name}.json")

                if not os.path.exists(old_path):
                    return all_histories, "❌ **Error:** Chat file not found", chat_id, gr.update()

                if os.path.exists(new_path):
                    return all_histories, "❌ **Error:** A chat with that name already exists", chat_id, gr.update()

                # Rename the file
                os.rename(old_path, new_path)

                # Update the all_histories dictionary
                if chat_id in all_histories:
                    all_histories[new_name] = all_histories.pop(chat_id)

                # Update dropdown choices
                chat_ids = list(all_histories.keys())
                # Ensure new_name is in the choices before setting it as value
                dropdown_value = new_name if new_name in chat_ids else None
                dropdown_update = gr.update(choices=chat_ids, value=dropdown_value)

                return all_histories, f"✅ **Chat renamed successfully** from '{chat_id}' to '{new_name}'", new_name, dropdown_update

            except Exception as e:
                return all_histories, f"❌ **Rename failed:** {str(e)}", chat_id, gr.update()

        rename_btn.click(
            fn=handle_rename_chat,
            inputs=[selected_chat_id, rename_box, all_histories, username_state],
            outputs=[all_histories, rename_status, selected_chat_id, chat_selector]
        )

        # Export functionality
        def handle_export_chats(username):
            if not username:
                return "❌ **Error:** Please log in first"

            try:
                from backend import render_all_chats
                import json
                from datetime import datetime

                chats = render_all_chats(username)
                if not chats:
                    return "ℹ️ **No chats to export**"

                export_data = {
                    "user": username,
                    "export_date": datetime.now().isoformat(),
                    "chats": chats
                }

                # In a real implementation, this would create a downloadable file
                chat_count = len(chats)
                return f"✅ **Export prepared!**\n\n**User:** {username}\n**Chats:** {chat_count}\n**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n*Note: Download functionality will be implemented in a future update.*"
            except Exception as e:
                return f"❌ **Export failed:** {str(e)}"

        export_btn.click(
            fn=handle_export_chats,
            inputs=[username_state],
            outputs=[export_status]
        )

        # Note: Removed automatic all_histories.change handler to prevent conflicts with rename function

        # Logout with improved state clearing
        def do_logout():
            return (
                False,  # logged_in_state
                "",     # username_state
                {},     # all_histories
                "",     # selected_chat_id
                gr.update(visible=True),   # login_container
                gr.update(visible=False),  # main_container
                gr.update(visible=False, value=""),  # error_message
                gr.update(choices=[], value=None),     # chat_selector
                gr.update(value=[]),       # chatbot
                gr.update(value=[]),       # file_chatbot
                gr.update(value=[]),       # audio_chatbot
                gr.update(value=""),       # search_results
                gr.update(value=""),       # rename_status
                gr.update(visible=False, value=""),  # file_status
                gr.update(visible=False, value=""),  # audio_status
                gr.update(visible=False, value=""),  # export_status
                gr.update(value=""),       # msg
                gr.update(value=""),       # search_box
                gr.update(value="")        # rename_box
            )
        logout_btn.click(
            fn=do_logout,
            outputs=[
                logged_in_state, username_state, all_histories, selected_chat_id,
                login_container, main_container, error_message, chat_selector, chatbot,
                file_chatbot, audio_chatbot, search_results, rename_status,
                file_status, audio_status, export_status, msg, search_box, rename_box
            ]
        )

        # Load function (moved from chat_interface.py)
        def on_start(username):
            if not username:
                return gr.update(choices=[], value=None), "", {}, []
            chats = load_all_chats(username)
            chat_ids = list(chats.keys())
            selected = chat_ids[0] if chat_ids else None
            dropdown_value = selected if selected in chat_ids else None
            return gr.update(choices=chat_ids, value=dropdown_value), selected or "", chats, chats[selected] if selected else []
        app.load(
            fn=on_start,
            inputs=[username_state],
            outputs=[chat_selector, selected_chat_id, all_histories, chatbot]
        )

    return app

if __name__ == "__main__":
    app = main_app()
    app.launch(debug=True, share=False)
