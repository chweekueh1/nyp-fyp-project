import gradio as gr
import asyncio
from typing import Dict, Any, Tuple
from backend import do_login as backend_login, do_register as backend_register

def login_interface(
    logged_in_state: gr.State,
    username_state: gr.State,
    main_container: gr.Column,
    login_container: gr.Column,
    error_message: gr.Markdown
) -> None:
    with login_container:
        username = gr.Textbox(label="Username", placeholder="Enter your username")
        password = gr.Textbox(label="Password", placeholder="Enter your password", type="password")
        login_btn = gr.Button("Login")
        register_btn = gr.Button("Register")
        
        def handle_login(username, password):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(backend_login(username, password))
            loop.close()
            if result.get("code") == "200":
                return True, username, gr.update(visible=False), gr.update(visible=True), gr.update(visible=False, value="")
            else:
                return False, "", gr.update(visible=True), gr.update(visible=False), gr.update(visible=True, value=result.get("message", "Login failed"))
        
        login_btn.click(
            fn=handle_login,
            inputs=[username, password],
            outputs=[logged_in_state, username_state, login_container, main_container, error_message]
        )
        
        def switch_to_register():
            return gr.update(visible=False), gr.update(visible=True)
        
        register_btn.click(
            fn=switch_to_register,
            outputs=[login_container, main_container]
        )

def register_interface(
    logged_in_state: gr.State,
    username_state: gr.State,
    main_container: gr.Column,
    register_container: gr.Column,
    error_message: gr.Markdown
) -> None:
    with register_container:
        username = gr.Textbox(label="Username", placeholder="Choose a username")
        password = gr.Textbox(label="Password", placeholder="Choose a password", type="password")
        confirm = gr.Textbox(label="Confirm Password", placeholder="Confirm password", type="password")
        register_btn = gr.Button("Register Account")
        back_btn = gr.Button("Back to Login")
        
        def handle_register(username, password, confirm):
            if not username or not password or not confirm:
                return False, "", gr.update(visible=True), gr.update(visible=False), gr.update(visible=True, value="All fields required")
            if password != confirm:
                return False, "", gr.update(visible=True), gr.update(visible=False), gr.update(visible=True, value="Passwords do not match")
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(backend_register(username, password))
            loop.close()
            if result.get("code") == "200":
                return False, "", gr.update(visible=True), gr.update(visible=False), gr.update(visible=True, value="Registration successful! Please log in.")
            else:
                return False, "", gr.update(visible=True), gr.update(visible=False), gr.update(visible=True, value=result.get("message", "Registration failed"))
        
        register_btn.click(
            fn=handle_register,
            inputs=[username, password, confirm],
            outputs=[logged_in_state, username_state, register_container, main_container, error_message]
        )
        
        def back_to_login():
            return gr.update(visible=False), gr.update(visible=True)
        
        back_btn.click(
            fn=back_to_login,
            outputs=[register_container, main_container]
        )
