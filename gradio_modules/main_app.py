# gradio_modules/main_app.py
import gradio as gr
import sys
from pathlib import Path
import os

# Add parent directory to path for imports
parent_dir = Path(__file__).parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from backend import list_user_chat_ids, get_chat_history, ask_question, CHAT_SESSIONS_PATH
from gradio_modules.login_and_register import login_interface, register_interface

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

def rename_chat(old_chat_id, new_chat_id, all_histories, username):
    if not old_chat_id:
        return all_histories, gr.update(value="No chat selected to rename."), old_chat_id
    if not new_chat_id:
        return all_histories, gr.update(value="Please enter a new chat name."), old_chat_id
    user_folder = os.path.join(CHAT_SESSIONS_PATH, username)
    old_path = os.path.join(user_folder, f"{old_chat_id}.json")
    new_path = os.path.join(user_folder, f"{new_chat_id}.json")
    if not os.path.exists(old_path):
        return all_histories, gr.update(value="Chat not found."), old_chat_id
    if os.path.exists(new_path):
        return all_histories, gr.update(value="A chat with that name already exists."), old_chat_id
    try:
        os.rename(old_path, new_path)
        all_histories[new_chat_id] = all_histories.pop(old_chat_id)
        return all_histories, gr.update(value="Chat renamed."), new_chat_id
    except Exception as e:
        return all_histories, gr.update(value=f"Rename failed: {e}"), old_chat_id

def main_app():
    with gr.Blocks() as app:
        # Inject external JS for keyboard shortcut (Ctrl+Shift+K)
        gr.HTML('<script src="/file/scripts/scripts.js"></script>')
        
        # States
        logged_in_state = gr.State(False)
        username_state = gr.State("")
        all_histories = gr.State({})
        selected_chat_id = gr.State("")
        
        # Containers
        with gr.Column(visible=True) as login_container:
            error_message = gr.Markdown(visible=False)
        with gr.Column(visible=False) as register_container:
            pass
        with gr.Column(visible=False) as main_container:
            user_info = gr.Markdown(visible=True)
            logout_btn = gr.Button("Logout")
            with gr.Row():
                chat_selector = gr.Dropdown(choices=[], label="Select Chat")
                new_chat_btn = gr.Button("New Chat")
            chatbot = gr.Chatbot(label="Chatbot")
            msg = gr.Textbox(label="Message", placeholder="Type your message here...")
            send_btn = gr.Button("Send")
            with gr.Row():
                search_box = gr.Textbox(label="Fuzzy Search (Ctrl+Shift+K)", placeholder="Fuzzy Search (Ctrl+Shift+K)")
                search_results = gr.Markdown()
            with gr.Row():
                rename_box = gr.Textbox(label="Rename Chat", placeholder="Enter new chat name")
                rename_btn = gr.Button("Rename")
                rename_status = gr.Markdown()

        # Login/Register UI
        login_interface(
            logged_in_state=logged_in_state,
            username_state=username_state,
            main_container=main_container,
            login_container=login_container,
            error_message=error_message
        )
        register_interface(
            logged_in_state=logged_in_state,
            username_state=username_state,
            main_container=main_container,
            register_container=register_container,
            error_message=error_message
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
                return {}, "", gr.update(choices=[], value=""), []
            chats = load_all_chats(username)
            chat_ids = list(chats.keys())
            selected = chat_ids[0] if chat_ids else ""
            return chats, selected, gr.update(choices=chat_ids, value=selected), chats[selected] if selected else []
        logged_in_state.change(
            fn=on_login,
            inputs=[logged_in_state, username_state],
            outputs=[all_histories, selected_chat_id, chat_selector, chatbot]
        )

        # New chat
        def start_new_chat(all_histories, username):
            new_id = create_new_chat_id()
            all_histories[new_id] = []
            return gr.update(choices=list(all_histories.keys()), value=new_id), new_id, all_histories, []
        new_chat_btn.click(
            start_new_chat,
            inputs=[all_histories, username_state],
            outputs=[chat_selector, selected_chat_id, all_histories, chatbot]
        )

        # Switch chat
        def switch_chat(chat_id, all_histories):
            return all_histories.get(chat_id, [])
        chat_selector.change(
            fn=switch_chat,
            inputs=[chat_selector, all_histories],
            outputs=[chatbot]
        )

        # Send message
        send_btn.click(
            fn=lambda msg, chat_id, all_histories, username: send_message_to_chat(msg, chat_id, all_histories, username),
            inputs=[msg, selected_chat_id, all_histories, username_state],
            outputs=[msg, all_histories, selected_chat_id, chatbot]
        )

        # Fuzzy search (Ctrl+Shift+K)
        search_box.submit(
            fn=fuzzy_find_chats,
            inputs=[search_box, all_histories],
            outputs=[search_results]
        )

        # Rename chat
        rename_btn.click(
            fn=lambda old_id, new_id, all_histories, username: rename_chat(old_id, new_id, all_histories, username),
            inputs=[selected_chat_id, rename_box, all_histories, username_state],
            outputs=[all_histories, rename_status, selected_chat_id]
        )

        # Update selector and chat when all_histories changes
        def update_selector_and_chat(all_histories, selected_chat_id):
            chat_ids = list(all_histories.keys())
            selected = selected_chat_id if selected_chat_id in chat_ids else (chat_ids[0] if chat_ids else "")
            return gr.update(choices=chat_ids, value=selected), all_histories.get(selected, [])
        all_histories.change(
            fn=update_selector_and_chat,
            inputs=[all_histories, selected_chat_id],
            outputs=[chat_selector, chatbot]
        )

        # Logout
        def do_logout():
            return (
                False, "", {}, "", gr.update(visible=True), gr.update(visible=False), gr.update(visible=False, value=""), gr.update(choices=[], value=""), gr.update(value=[]), gr.update(value=""), gr.update(value="")
            )
        logout_btn.click(
            fn=do_logout,
            outputs=[
                logged_in_state, username_state, all_histories, selected_chat_id,
                login_container, main_container, error_message, chat_selector, chatbot, search_results, rename_status
            ]
        )

    return app

if __name__ == "__main__":
    app = main_app()
    app.launch(debug=True, share=False)
