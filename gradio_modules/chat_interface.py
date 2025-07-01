#!/usr/bin/env python3
import gradio as gr
from backend import (
    list_user_chat_ids,
    get_chat_history,
    ask_question,
    create_and_persist_new_chat,
)
import asyncio
import sys
from pathlib import Path
from infra_utils import setup_logging

# Add parent directory to path for imports
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Now import from parent directory

# Set up logging
logger = setup_logging()


# Module-level function for testing
async def _handle_chat_message(
    message: str,
    chat_history: list,
    username: str,
    chat_id: str,
) -> tuple[str, list, dict, str]:
    """
    Handle chat message processing - module level function for testing.

    :param message: The message to process.
    :type message: str
    :param chat_history: The current chat history.
    :type chat_history: list
    :param username: The username of the user.
    :type username: str
    :param chat_id: The chat ID.
    :type chat_id: str
    :return: Tuple containing updated message, chat history, error dict, and chat ID.
    :rtype: tuple[str, list, dict, str]
    """
    from backend import ask_question, create_and_persist_new_chat

    if not message.strip():
        return (
            "",
            chat_history,
            {"visible": True, "value": "Please enter a message."},
            chat_id,
        )
    if not chat_id:
        chat_id = create_and_persist_new_chat(username)
        chat_history = []
    result = await ask_question(message, chat_id, username)
    if result.get("code") == "200":
        answer = result.get("response", "")
        if isinstance(answer, dict) and "answer" in answer:
            answer = answer["answer"]
        chat_history.append([message, answer])
        return "", chat_history, {"visible": False, "value": ""}, chat_id
    else:
        chat_history.append([message, f"Error: {result.get('error', 'Unknown error')}"])
        return (
            "",
            chat_history,
            {"visible": True, "value": result.get("error", "Unknown error")},
            chat_id,
        )


def chat_interface(
    logged_in_state: gr.State,
    username_state: gr.State,
    current_chat_id_state: gr.State,
    chat_history_state: gr.State,
) -> None:
    """
    Create the chat interface components.

    :param logged_in_state: State for tracking login status.
    :type logged_in_state: gr.State
    :param username_state: State for storing current username.
    :type username_state: gr.State
    :param current_chat_id_state: State for storing current chat ID.
    :type current_chat_id_state: gr.State
    :param chat_history_state: State for storing chat history.
    :type chat_history_state: gr.State
    :return: None
    """
    with gr.Row():
        chat_selector = gr.Dropdown(choices=[], label="Select Chat")
        new_chat_btn = gr.Button("New Chat")
    chatbot = gr.Chatbot(label="Chatbot", type="messages")
    msg = gr.Textbox(label="Message", placeholder="Type your message here...")
    send_btn = gr.Button("Send")
    with gr.Row(visible=False, elem_id="search-row"):
        search_box = gr.Textbox(
            label="Fuzzy Search (Ctrl+Shift+K or Alt+K)",
            placeholder="Fuzzy Search (Ctrl+Shift+K or Alt+K)",
        )
        search_results = gr.Markdown()

    def load_all_chats(username):
        chat_ids = list_user_chat_ids(username)
        all_histories = {}
        for cid in chat_ids:
            try:
                hist = get_chat_history(cid, username)
                # Convert tuples to messages format
                if hist:
                    messages = []
                    for pair in hist:
                        messages.append({"role": "user", "content": pair[0]})
                        messages.append({"role": "assistant", "content": pair[1]})
                    all_histories[cid] = messages
                else:
                    all_histories[cid] = []
            except Exception as e:
                all_histories[cid] = [
                    {"role": "user", "content": "[Error loading chat]"},
                    {"role": "assistant", "content": str(e)},
                ]
        return all_histories

    def on_start(username):
        all_histories = load_all_chats(username)
        chat_ids = list(all_histories.keys())
        selected = chat_ids[0] if chat_ids else ""
        return (
            gr.update(choices=chat_ids, value=selected),
            selected,
            all_histories,
            all_histories[selected] if selected else [],
        )

    def start_new_chat(all_histories, username):
        new_id = create_and_persist_new_chat(username)
        all_histories[new_id] = []
        return (
            gr.update(choices=list(all_histories.keys()), value=new_id),
            new_id,
            all_histories,
            [],
        )

    new_chat_btn.click(
        start_new_chat,
        inputs=[chat_history_state, username_state],
        outputs=[chat_selector, current_chat_id_state, chat_history_state, chatbot],
    )

    def switch_chat(chat_id, all_histories):
        return chat_id, all_histories.get(chat_id, [])

    chat_selector.change(
        fn=switch_chat,
        inputs=[chat_selector, chat_history_state],
        outputs=[current_chat_id_state, chatbot],
    )

    def send_message_to_chat(message, chat_id, all_histories, username):
        if not message.strip():
            return (
                "",
                all_histories,
                chat_id,
                [
                    {"role": "user", "content": ""},
                    {"role": "assistant", "content": "Please enter a message."},
                ],
            )
        if not chat_id:
            chat_id = create_and_persist_new_chat(username)
            all_histories[chat_id] = []
        result = asyncio.run(ask_question(message, chat_id, username))
        if result.get("code") == "200":
            answer = result.get("response", "")
            if isinstance(answer, dict) and "answer" in answer:
                answer = answer["answer"]
            all_histories[chat_id].extend(
                [
                    {"role": "user", "content": message},
                    {"role": "assistant", "content": answer},
                ]
            )
        else:
            all_histories[chat_id].extend(
                [
                    {"role": "user", "content": message},
                    {
                        "role": "assistant",
                        "content": f"Error: {result.get('error', 'Unknown error')}",
                    },
                ]
            )
        return "", all_histories, chat_id, all_histories[chat_id]

    send_btn.click(
        fn=send_message_to_chat,
        inputs=[msg, current_chat_id_state, chat_history_state, username_state],
        outputs=[msg, chat_history_state, current_chat_id_state, chatbot],
    )

    def fuzzy_find_chats(query, all_histories):
        from difflib import get_close_matches

        results = []
        for cid, history in all_histories.items():
            # Extract content from messages format
            all_text = " ".join(
                [msg.get("content", "") for msg in history if isinstance(msg, dict)]
            )
            if query.lower() in all_text.lower() or get_close_matches(
                query, [all_text], n=1, cutoff=0.6
            ):
                results.append(f"Chat {cid}: {all_text[:100]}...")
        return "\n\n".join(results) if results else "No matching chats found."

    search_box.submit(
        fn=fuzzy_find_chats,
        inputs=[search_box, chat_history_state],
        outputs=[search_results],
    )
