import gradio as gr
import sys
from pathlib import Path
import os
import json

# Add parent directory to path for imports
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from backend import list_user_chat_ids, get_chat_history, ask_question

USERNAME = "test"

def load_all_chats(username):
    """Load all chat histories for a user."""
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

def send_message_to_chat(message, chat_id, all_histories):
    if not message.strip():
        return "", all_histories, chat_id, [["", "Please enter a message."]]
    if not chat_id:
        chat_id = create_new_chat_id()
        all_histories[chat_id] = []
    try:
        import asyncio
        result = asyncio.run(ask_question(message, chat_id, USERNAME))
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

with gr.Blocks() as app:
    gr.HTML('<script src="/file/scripts/scripts.js"></script>')

    all_histories = gr.State(load_all_chats(USERNAME))
    selected_chat_id = gr.State("")
    with gr.Row():
        chat_selector = gr.Dropdown(choices=[], label="Select Chat")
        new_chat_btn = gr.Button("New Chat")
    chatbot = gr.Chatbot(label="Chatbot")
    msg = gr.Textbox(label="Message", placeholder="Type your message here...")
    send_btn = gr.Button("Send")
    # Fuzzy search UI, initially hidden
    with gr.Row(visible=False, elem_id="search-row") as search_row:
        search_box = gr.Textbox(label="Fuzzy Search (Ctrl+Shift+K or Alt+K)", placeholder="Fuzzy Search (Ctrl+Shift+K or Alt+K)")
        search_results = gr.Markdown()

    # Load tabs and chat history on app start or when chats change
    def on_start(all_histories):
        chat_ids = list(all_histories.keys())
        selected = chat_ids[0] if chat_ids else ""
        return gr.update(choices=chat_ids, value=selected), selected, all_histories, all_histories[selected] if selected else []

    app.load(on_start, inputs=[all_histories], outputs=[chat_selector, selected_chat_id, all_histories, chatbot])

    # New chat
    def start_new_chat(all_histories):
        new_id = create_new_chat_id()
        all_histories[new_id] = []
        # Persist the new chat session to disk
        user_folder = os.path.join("data", "chat_sessions", USERNAME)
        os.makedirs(user_folder, exist_ok=True)
        chat_file = os.path.join(user_folder, f"{new_id}.json")
        with open(chat_file, "w", encoding="utf-8") as f:
            # Save as the same format your backend expects (list of messages or dict with "messages")
            json.dump({"messages": []}, f, indent=2)
        return gr.update(choices=list(all_histories.keys()), value=new_id), new_id, all_histories, []

    new_chat_btn.click(
        start_new_chat,
        inputs=[all_histories],
        outputs=[chat_selector, selected_chat_id, all_histories, chatbot]
    )

    # Switch chat (update both selected_chat_id and chatbot)
    def switch_chat(chat_id, all_histories):
        return chat_id, all_histories.get(chat_id, [])

    chat_selector.change(
        fn=switch_chat,
        inputs=[chat_selector, all_histories],
        outputs=[selected_chat_id, chatbot]
    )

    # Send message
    send_btn.click(
        fn=send_message_to_chat,
        inputs=[msg, selected_chat_id, all_histories],
        outputs=[msg, all_histories, selected_chat_id, chatbot]
    )

    # Fuzzy search (triggered by Ctrl+Shift+K or Alt+K focusing the box, then Enter)
    search_box.submit(
        fn=fuzzy_find_chats,
        inputs=[search_box, all_histories],
        outputs=[search_results]
    )

if __name__ == "__main__":
    app.launch(debug=True, share=False)