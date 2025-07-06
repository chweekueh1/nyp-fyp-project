# gradio_modules/chatbot.py
#!/usr/bin/env python3

"""
Chatbot Interface Module

This module provides the main chatbot interface for the NYP FYP Chatbot application.
Users can send messages, manage chat sessions, search history, and rename chats.
"""

from typing import Tuple, Dict, Any

import gradio as gr

# Import clear_chat_history from infra_utils
from infra_utils import clear_chat_history

from backend.chat import (
    ask_question,
    list_user_chat_ids,
    get_chat_history,
    get_chat_name,
    create_and_persist_new_chat,
    rename_chat,
    search_chat_history,
    ensure_chat_on_login,
)


# Function to load all chats (moved outside chatbot_ui)
def load_all_chats(username: str) -> Dict[str, Dict[str, Any]]:
    """Load all chat histories for a user.

    Args:
        username: The username to load chats for

    Returns:
        Dictionary mapping chat_id to a dictionary containing chat history (list of [user_msg, bot_msg] pairs) and name.
    """
    if not username:
        return {}

    chat_ids = list_user_chat_ids(username)
    all_histories = {}
    for cid in chat_ids:
        try:
            hist = get_chat_history(cid, username)
            chat_name = get_chat_name(cid, username)
            all_histories[cid] = {
                "history": [list(pair) for pair in hist] if hist else [],
                "name": chat_name or cid,
            }
        except Exception as e:
            all_histories[cid] = {
                "history": [["[Error loading chat]", str(e)]],
                "name": cid,
            }
    return all_histories


# Function to update chat memory and dropdown (moved outside chatbot_ui)
def update_chat_memory_and_dropdown(username: str, current_chat_id: str = "") -> Tuple:
    """
    Helper function to update the chat selector dropdown and the chatbot display,
    and control interactivity of the chat input.

    Args:
        username: The current logged-in username.
        current_chat_id: The ID of the currently active chat, if any.

    Returns:
        Tuple: Gradio updates for chat_selector, the new selected_chat_id,
               the history for the selected chat, the updated all_chats_data_state,
               and interactive states for chat_input and send_btn.
    """
    all_chats = load_all_chats(username)
    chat_ids = list(all_chats.keys())
    chat_choices = [(all_chats[cid].get("name", cid), cid) for cid in chat_ids]
    chat_choices.sort(key=lambda x: x[0].lower())

    selected = None
    if current_chat_id and current_chat_id in chat_ids:
        selected = current_chat_id
    elif chat_ids:
        # If no specific chat is requested or current one is invalid, select the first one
        selected = chat_choices[0][1]  # Use the ID from the sorted choices

    messages_history = (
        all_chats.get(selected, {}).get("history", []) if selected else []
    )

    # Determine interactivity based on whether a chat is selected
    is_interactive = selected is not None

    return (
        gr.update(choices=chat_choices, value=selected),  # chat_selector update
        selected,  # new selected_chat_id
        messages_history,  # chatbot history update
        all_chats,  # all_chats_data_state update
        gr.update(interactive=is_interactive),  # chat_input interactivity
        gr.update(interactive=is_interactive),  # send_btn interactivity
    )


# This function ensures a chat exists and then updates the UI
def ensure_chat_on_login_and_update_memory(username: str):
    """
    Called on user login. Ensures a chat session exists and updates the UI elements.
    """
    if not username:
        # If no username, clear UI elements and disable input
        return (
            gr.update(choices=[], value=None),  # chat_selector
            "",  # chat_id_state
            [],  # chatbot
            {},  # all_chats_data_state
            gr.update(interactive=False),  # chat_input
            gr.update(interactive=False),  # send_btn
        )

    # First, ensure a chat session exists in the backend
    ensured_chat_id = ensure_chat_on_login(username)

    # Then, update the UI based on all chats, focusing on the ensured_chat_id
    (
        chat_selector_update,
        selected_chat_id,
        messages_history,
        all_chats,
        chat_input_interactive,
        send_btn_interactive,
    ) = update_chat_memory_and_dropdown(username, ensured_chat_id)

    return (
        chat_selector_update,
        selected_chat_id,
        messages_history,
        all_chats,
        chat_input_interactive,
        send_btn_interactive,
    )


def handle_search(username: str, query: str) -> str:
    """
    Handle search query and return formatted results.

    Args:
        username: The username to search for
        query: The search query string

    Returns:
        Formatted string containing search results
    """
    if not username or not query.strip():
        return "Please enter a search query."

    try:
        # Get search results from backend
        results = search_chat_history(query.strip(), username)

        if not results:
            return f"No results found for '{query}'."

        # Format results for display
        formatted_results = [f"# 🔍 Search Results for '{query}'\n"]
        formatted_results.append(
            f"Found {len(results)} chat(s) with matching content:\n"
        )

        for i, result in enumerate(results, 1):
            chat_name = result["chat_name"]
            match_count = result["match_count"]
            chat_preview = result["chat_preview"]

            formatted_results.append(f"## {i}. {chat_name}")
            formatted_results.append(
                f"**Matches:** {match_count} | **Preview:** {chat_preview}"
            )

            # Show first few matching messages
            for match in result["matching_messages"][:2]:  # Show max 2 matches per chat
                user_msg = match["user_message"]
                bot_msg = match["bot_message"]

                if match["user_match"]:
                    formatted_results.append(f"**User:** {user_msg}")
                if match["bot_match"]:
                    formatted_results.append(f"**Bot:** {bot_msg}")

            if len(result["matching_messages"]) > 2:
                remaining = len(result["matching_messages"]) - 2
                formatted_results.append(f"*... and {remaining} more matches*")

            formatted_results.append("---")
        return "\n".join(formatted_results)
    except Exception as e:
        return f"Error searching: {str(e)}"


def chatbot_ui(
    username_state: gr.State,
    chat_history_state: gr.State,
    chat_id_state: gr.State,
    setup_events: bool = True,
) -> Tuple:
    """
    Create the chatbot UI components.

    Args:
        username_state (gr.State): State containing the username.
        chat_history_state (gr.State): State containing the chat history.
        chat_id_state (gr.State): State containing the current chat ID.
        setup_events (bool): Whether to set up event listeners. Default is True.

    Returns:
        Tuple: A tuple of Gradio components.
    """
    with gr.Blocks():  # Removed 'as demo' - no longer needed for F841
        # States for managing chat sessions and user data
        # logged_in_state = gr.State(False) # Removed this unused variable for F841
        all_chats_data_state = gr.State({})  # Stores {chat_id: {name, history...}}

        with gr.Row():
            with gr.Column(scale=1):
                with gr.Column():
                    gr.Markdown("## Chat Sessions")
                    chat_selector = gr.Dropdown(
                        label="Select Chat",
                        choices=[],
                        value=None,
                        interactive=True,
                        allow_custom_value=False,
                    )
                    new_chat_btn = gr.Button("➕ New Chat")
                    rename_input = gr.Textbox(
                        label="Rename Current Chat",
                        placeholder="Enter new chat name...",
                    )
                    rename_btn = gr.Button("Rename Chat")
                    debug_md = gr.Markdown("")  # For debugging messages

                    # Clear Chat History button
                    clear_chat_btn = gr.Button("🗑️ Clear Chat History")
                    clear_chat_status = gr.Markdown("")

                with gr.Accordion("Search Chat History", open=False):
                    search_input = gr.Textbox(
                        label="Search chats", placeholder="Enter search query..."
                    )
                    search_btn = gr.Button("Search")
                    search_results = gr.Markdown("")

            with gr.Column(scale=3):
                chatbot = gr.Chatbot(
                    height=500, label="Chat History", show_copy_button=True
                )
                with gr.Row():
                    chat_input = gr.Textbox(
                        label="Message",
                        placeholder="Type your message here...",
                        scale=7,
                        container=False,
                        interactive=False,  # Set to False initially
                    )
                    send_btn = gr.Button(
                        "Send", scale=1, interactive=False
                    )  # Set to False initially

        if setup_events:
            # Link username state change to UI updates for chat
            username_state.change(
                fn=ensure_chat_on_login_and_update_memory,
                inputs=[username_state],
                outputs=[
                    chat_selector,
                    chat_id_state,
                    chatbot,
                    all_chats_data_state,
                    chat_input,
                    send_btn,
                ],
            )

            # Clear Chat History button
            clear_chat_btn.click(
                fn=lambda username, chat_id: (
                    clear_chat_history(chat_id, username),
                    gr.update(value=[]),  # Clear chatbot display
                    "Chat history cleared!",
                    *update_chat_memory_and_dropdown(
                        username, chat_id
                    ),  # Refresh dropdown
                ),
                inputs=[username_state, chat_id_state],
                outputs=[
                    chatbot,
                    clear_chat_status,
                    chat_selector,
                    chat_id_state,
                    all_chats_data_state,
                    chat_input,
                    send_btn,
                ],
            )

            # New Chat Button
            new_chat_btn.click(
                fn=lambda username: (
                    create_and_persist_new_chat(username),
                    *update_chat_memory_and_dropdown(
                        username
                    ),  # Refresh dropdown and select new chat
                ),
                inputs=[username_state],
                outputs=[
                    gr.State(None),  # Dummy state for backend call return
                    chat_selector,
                    chat_id_state,
                    chatbot,
                    all_chats_data_state,
                    chat_input,
                    send_btn,
                ],
                show_progress=False,
            )

            # Rename Chat Button
            rename_btn.click(
                fn=lambda chat_id, username, new_name: (
                    rename_chat(chat_id, username, new_name),
                    *update_chat_memory_and_dropdown(
                        username, chat_id
                    ),  # Refresh dropdown and maintain current chat
                ),
                inputs=[chat_id_state, username_state, rename_input],
                outputs=[
                    gr.State(None),  # Dummy state for backend call return
                    chat_selector,
                    chat_id_state,
                    chatbot,
                    all_chats_data_state,
                    chat_input,
                    send_btn,
                ],
                show_progress=False,
            )

            # Function to process and send messages
            async def process_message(message, current_history, username, chat_id):
                # Await the asynchronous ask_question function
                result_from_ask_question = await ask_question(
                    message, chat_id, username
                )

                # Safely get the bot's response
                answer = result_from_ask_question.get("response", {}).get(
                    "answer", "Error getting response."
                )

                # Check for errors from ask_question and update history accordingly
                if result_from_ask_question.get("code") != "200":
                    error_msg = result_from_ask_question.get(
                        "error", "An unknown error occurred."
                    )
                    answer = f"Error: {error_msg}"  # Display error to user

                new_history_entry = [message, answer]  # Correctly use 'answer' here
                updated_history = current_history + [new_history_entry]

                return (
                    "",
                    updated_history,
                    updated_history,
                )  # Clear input, update chatbot, update history state

            # Send message logic
            send_btn.click(
                fn=process_message,
                inputs=[chat_input, chatbot, username_state, chat_id_state],
                outputs=[chat_input, chatbot, chat_history_state],
                show_progress=True,
            )

            chat_input.submit(
                fn=process_message,
                inputs=[chat_input, chatbot, username_state, chat_id_state],
                outputs=[chat_input, chatbot, chat_history_state],
                show_progress=True,
            )

            # Chat selector logic
            chat_selector.change(
                fn=lambda chat_id, all_chats: (
                    all_chats.get(chat_id, {}).get("history", []),
                    chat_id,
                    gr.update(
                        interactive=True
                    ),  # Enable chat input when a chat is selected
                    gr.update(
                        interactive=True
                    ),  # Enable send button when a chat is selected
                ),
                inputs=[chat_selector, all_chats_data_state],
                outputs=[chatbot, chat_id_state, chat_input, send_btn],
                show_progress=False,
            )

            # Search history
            search_btn.click(
                fn=handle_search,
                inputs=[username_state, search_input],
                outputs=[search_results],
            )
            search_input.submit(
                fn=handle_search,
                inputs=[username_state, search_input],
                outputs=[search_results],
            )

    return (
        chat_selector,
        chatbot,
        chat_input,
        send_btn,
        search_input,
        search_btn,
        search_results,
        rename_input,
        rename_btn,
        debug_md,
        clear_chat_btn,
        clear_chat_status,
        new_chat_btn,
    )
