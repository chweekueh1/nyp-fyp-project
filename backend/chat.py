#!/usr/bin/env python3
"""
Chat module for the backend.
Contains chat-related functions for handling conversations and chat history.
"""

import os
import json
import logging
import re
from typing import List, Tuple, Dict, Any
from .config import CHAT_DATA_PATH, CHAT_SESSIONS_PATH
from .rate_limiting import check_rate_limit, get_rate_limit_info
from .utils import sanitize_input, save_message_async
from .database import get_llm_functions
from .timezone_utils import get_utc_timestamp, now_singapore

# Set up logging
logger = logging.getLogger(__name__)


async def ask_question(
    question: str, chat_id: str, username: str
) -> dict[str, str | dict]:
    """Ask a question and get a response from the chatbot."""
    logging.error(
        f"ask_question called with question={question!r}, chat_id={chat_id!r}, username={username!r}"
    )
    if not question or not chat_id or not username:
        return {"error": "Invalid question or chat_id or username", "code": "400"}
    if not await check_rate_limit(username, "chat"):
        rate_limit_info = get_rate_limit_info("chat")
        return {
            "error": f"Rate limit exceeded. Please wait {rate_limit_info['time_window']} seconds.",
            "code": "429",
        }
    sanitized_question = sanitize_input(question)
    try:
        # Get LLM functions lazily
        llm_funcs = get_llm_functions()
        if not llm_funcs or not llm_funcs["is_llm_ready"]():
            logging.error(
                "LLM/DB not ready in ask_question. Backend may not be fully initialized."
            )
            return {
                "error": "AI assistant is not fully initialized. Please try again later.",
                "code": "500",
            }
        response = llm_funcs["get_convo_hist_answer"](sanitized_question, chat_id)
        # Save user message
        await save_message_async(
            username, chat_id, {"role": "user", "content": sanitized_question}
        )
        # Save bot response
        if isinstance(response, dict) and "answer" in response:
            answer = response["answer"]
        else:
            answer = str(response)
        await save_message_async(
            username, chat_id, {"role": "assistant", "content": answer}
        )
        return {"status": "OK", "code": "200", "response": response}
    except Exception as e:
        logging.error(f"Error in ask_question: {e}")
        return {"error": str(e), "code": "500"}


async def get_chatbot_response(ui_state: dict) -> dict:
    """
    Chatbot interface: generates a response using the LLM and updates history.
    Now includes message persistence to chat session files.
    """
    print(f"[DEBUG] backend.get_chatbot_response called with ui_state: {ui_state}")
    username = ui_state.get("username")
    message = ui_state.get("message")
    history = ui_state.get("history", [])
    chat_id = ui_state.get("chat_id", "default")

    if not message:
        return {
            "history": history,
            "response": "[No message provided]",
            "debug": "No message.",
        }

    if not username:
        return {
            "history": history,
            "response": "[Error] Username required for message persistence",
            "debug": "No username provided.",
        }

    # Check rate limit for chat operations
    if not await check_rate_limit(username, "chat"):
        rate_limit_info = get_rate_limit_info("chat")
        return {
            "history": history,
            "response": f"[Error] Rate limit exceeded. Please wait {rate_limit_info['time_window']} seconds.",
            "debug": "Rate limit exceeded.",
        }

    try:
        # Use your LLM chat model with lazy loading
        llm_funcs = get_llm_functions()
        if not llm_funcs:
            return {
                "history": history,
                "response": "AI assistant not available.",
                "debug": "LLM functions not loaded.",
            }

        result = llm_funcs["get_convo_hist_answer"](message, chat_id)
        response = result["answer"]

        # Update in-memory history
        history = history + [[message, response]]

        # Persist messages to chat session file asynchronously
        try:
            # Save user message
            await save_message_async(
                username, chat_id, {"role": "user", "content": message}
            )
            # Save bot response
            await save_message_async(
                username, chat_id, {"role": "assistant", "content": response}
            )
            print(f"[DEBUG] Messages persisted to chat session {chat_id}")
        except Exception as persist_error:
            print(f"[WARNING] Failed to persist messages: {persist_error}")
            # Continue anyway since we have the response

        response_dict = {
            "history": history,
            "response": response,
            "debug": "Chatbot response generated and persisted.",
        }
        print(f"[DEBUG] backend.get_chatbot_response returning: {response_dict}")
        return response_dict
    except Exception as e:
        print(f"[ERROR] backend.get_chatbot_response exception: {e}")
        return {
            "history": history,
            "response": f"[Error] {e}",
            "debug": f"Exception: {e}",
        }


def get_chat_response(message: str, username: str) -> str:
    """Get a simple chat response without persistence."""
    try:
        llm_funcs = get_llm_functions()
        if not llm_funcs:
            return "AI assistant not available."

        result = llm_funcs["get_convo_hist_answer"](message, "default")
        return result["answer"]
    except Exception as e:
        logger.error(f"Error in get_chat_response: {e}")
        return f"Error: {e}"


def search_chat_history(query: str, username: str) -> List[Dict[str, Any]]:
    """Search through user's chat history."""
    try:
        user_folder = os.path.join(CHAT_DATA_PATH, username)
        if not os.path.exists(user_folder):
            return []

        # Return empty results for empty query
        if not query or not query.strip():
            return []

        results = []
        query_lower = query.lower().strip()

        for filename in os.listdir(user_folder):
            if filename.endswith(".json"):
                chat_file = os.path.join(user_folder, filename)
                try:
                    with open(chat_file, "r") as f:
                        chat_data = json.load(f)

                    messages = chat_data.get("messages", [])
                    for message in messages:
                        content = message.get("content", "").lower()
                        if query_lower in content:
                            results.append(
                                {
                                    "chat_id": filename.replace(".json", ""),
                                    "message": message,
                                    "timestamp": message.get("timestamp", ""),
                                }
                            )
                except Exception as e:
                    logger.error(f"Error reading chat file {chat_file}: {e}")
                    continue

        # Sort by timestamp (newest first)
        results.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return results[:50]  # Limit to 50 results

    except Exception as e:
        logger.error(f"Error in search_chat_history: {e}")
        return []


def get_chat_history(chat_id: str, username: str) -> List[Tuple[str, str]]:
    """Get chat history for a specific chat."""
    try:
        user_folder = os.path.join(CHAT_DATA_PATH, username)
        chat_file = os.path.join(user_folder, f"{chat_id}.json")

        if not os.path.exists(chat_file):
            return []

        with open(chat_file, "r") as f:
            chat_data = json.load(f)

        messages = chat_data.get("messages", [])
        history = []

        for message in messages:
            role = message.get("role", "")
            content = message.get("content", "")
            if role in ["user", "assistant"]:
                history.append((role, content))

        return history

    except Exception as e:
        logger.error(f"Error in get_chat_history: {e}")
        return []


def list_user_chat_ids(username: str) -> list:
    """List all chat IDs for a user."""
    try:
        user_folder = os.path.join(CHAT_DATA_PATH, username)
        if not os.path.exists(user_folder):
            return []

        chat_ids = []
        for filename in os.listdir(user_folder):
            if filename.endswith(".json"):
                chat_id = filename.replace(".json", "")
                chat_ids.append(chat_id)

        return chat_ids

    except Exception as e:
        logger.error(f"Error in list_user_chat_ids: {e}")
        return []


def create_new_chat_id(username: str) -> str:
    """Create a new chat ID for a user."""
    try:
        # Use Singapore timezone for chat ID generation
        timestamp = now_singapore().strftime("%Y%m%d_%H%M%S")
        chat_id = f"chat_{timestamp}"

        # Ensure the chat file exists
        user_folder = os.path.join(CHAT_DATA_PATH, username)
        os.makedirs(user_folder, exist_ok=True)

        chat_file = os.path.join(user_folder, f"{chat_id}.json")
        if not os.path.exists(chat_file):
            with open(chat_file, "w") as f:
                json.dump({"messages": []}, f)

        return chat_id

    except Exception as e:
        logger.error(f"Error in create_new_chat_id: {e}")
        return f"chat_{int(now_singapore().timestamp())}"


def generate_smart_chat_name(first_message: str) -> str:
    """Generate a smart chat name based on the first message."""
    try:
        # Clean the message
        cleaned = re.sub(r"[^\w\s]", "", first_message)
        words = cleaned.split()

        # Filter out common stop words and short words
        stop_words = {
            "how",
            "do",
            "i",
            "a",
            "an",
            "the",
            "is",
            "are",
            "can",
            "you",
            "me",
            "with",
            "what",
            "where",
            "when",
            "why",
            "help",
        }
        meaningful_words = [
            w for w in words if len(w) > 2 and w.lower() not in stop_words
        ]

        # Take up to 4 meaningful words to capture more context
        selected_words = meaningful_words[:4]

        if selected_words:
            name = " ".join(selected_words).title()
            # Limit length
            if len(name) > 30:
                name = name[:27] + "..."
            return name
        else:
            return "New Chat"

    except Exception as e:
        logger.error(f"Error in generate_smart_chat_name: {e}")
        return "New Chat"


def create_and_persist_new_chat(username: str) -> str:
    """Create a new chat and persist it."""
    try:
        chat_id = create_new_chat_id(username)

        # Ensure the sessions directory exists
        os.makedirs(CHAT_SESSIONS_PATH, exist_ok=True)

        # Create session file
        session_file = os.path.join(CHAT_SESSIONS_PATH, f"{username}_{chat_id}.json")

        session_data = {
            "chat_id": chat_id,
            "username": username,
            "created_at": get_utc_timestamp(),
            "name": "New Chat",
        }

        with open(session_file, "w") as f:
            json.dump(session_data, f, indent=2)

        return chat_id

    except Exception as e:
        logger.error(f"Error in create_and_persist_new_chat: {e}")
        return create_new_chat_id(username)


def create_and_persist_smart_chat(username: str, first_message: str) -> str:
    """Create a new chat with a smart name based on the first message."""
    try:
        chat_id = create_new_chat_id(username)
        chat_name = generate_smart_chat_name(first_message)

        # Ensure the sessions directory exists
        os.makedirs(CHAT_SESSIONS_PATH, exist_ok=True)

        # Create session file
        session_file = os.path.join(CHAT_SESSIONS_PATH, f"{username}_{chat_id}.json")

        session_data = {
            "chat_id": chat_id,
            "username": username,
            "created_at": get_utc_timestamp(),
            "name": chat_name,
            "first_message": first_message,
        }

        with open(session_file, "w") as f:
            json.dump(session_data, f, indent=2)

        return chat_id

    except Exception as e:
        logger.error(f"Error in create_and_persist_smart_chat: {e}")
        return create_new_chat_id(username)


def get_user_chats(username: str) -> list:
    """Get all chats for a user."""
    try:
        session_files = []

        if os.path.exists(CHAT_SESSIONS_PATH):
            for filename in os.listdir(CHAT_SESSIONS_PATH):
                if filename.startswith(f"{username}_") and filename.endswith(".json"):
                    session_files.append(filename)

        return session_files

    except Exception as e:
        logger.error(f"Error in get_user_chats: {e}")
        return []


def get_user_chats_with_names(username: str) -> list:
    """Get all chats for a user with their names."""
    try:
        session_files = get_user_chats(username)
        chats = []

        for filename in session_files:
            session_file = os.path.join(CHAT_SESSIONS_PATH, filename)
            try:
                with open(session_file, "r") as f:
                    session_data = json.load(f)

                chats.append(
                    {
                        "chat_id": session_data.get("chat_id", ""),
                        "name": session_data.get("name", "New Chat"),
                        "created_at": session_data.get("created_at", ""),
                        "filename": filename,
                    }
                )
            except Exception as e:
                logger.error(f"Error reading session file {session_file}: {e}")
                continue

        # Sort by creation date (newest first)
        chats.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return chats

    except Exception as e:
        logger.error(f"Error in get_user_chats_with_names: {e}")
        return []


def get_chat_name(chat_id: str, username: str) -> str:
    """Get the name of a specific chat."""
    try:
        session_file = os.path.join(CHAT_SESSIONS_PATH, f"{username}_{chat_id}.json")

        if os.path.exists(session_file):
            with open(session_file, "r") as f:
                session_data = json.load(f)
            return session_data.get("name", "New Chat")
        else:
            return "New Chat"

    except Exception as e:
        logger.error(f"Error in get_chat_name: {e}")
        return "New Chat"


def set_chat_name(chat_id: str, username: str, new_name: str) -> bool:
    """Set the name of a specific chat."""
    try:
        session_file = os.path.join(CHAT_SESSIONS_PATH, f"{username}_{chat_id}.json")

        if os.path.exists(session_file):
            with open(session_file, "r") as f:
                session_data = json.load(f)

            session_data["name"] = new_name

            with open(session_file, "w") as f:
                json.dump(session_data, f, indent=2)

            return True
        else:
            return False

    except Exception as e:
        logger.error(f"Error in set_chat_name: {e}")
        return False


def rename_chat(old_chat_id: str, new_chat_name: str, username: str) -> Dict[str, Any]:
    """Rename a chat."""
    try:
        # Validate new name
        if not new_chat_name or len(new_chat_name.strip()) == 0:
            return {"success": False, "error": "Chat name cannot be empty"}

        new_chat_name = new_chat_name.strip()
        if len(new_chat_name) > 50:
            return {"success": False, "error": "Chat name too long (max 50 characters)"}

        # Check if chat exists
        old_session_file = os.path.join(
            CHAT_SESSIONS_PATH, f"{username}_{old_chat_id}.json"
        )
        if not os.path.exists(old_session_file):
            return {"success": False, "error": "Chat not found"}

        # Read current session data
        with open(old_session_file, "r") as f:
            session_data = json.load(f)

        # Update name
        session_data["name"] = new_chat_name

        # Save updated session data
        with open(old_session_file, "w") as f:
            json.dump(session_data, f, indent=2)

        logger.info(
            f"Chat {old_chat_id} renamed to '{new_chat_name}' for user {username}"
        )
        return {"success": True, "new_name": new_chat_name}

    except Exception as e:
        logger.error(f"Error in rename_chat: {e}")
        return {"success": False, "error": str(e)}


def rename_chat_file(old_chat_id: str, new_chat_id: str, username: str) -> bool:
    """Rename a chat file (internal function)."""
    try:
        old_session_file = os.path.join(
            CHAT_SESSIONS_PATH, f"{username}_{old_chat_id}.json"
        )
        new_session_file = os.path.join(
            CHAT_SESSIONS_PATH, f"{username}_{new_chat_id}.json"
        )

        if os.path.exists(old_session_file):
            os.rename(old_session_file, new_session_file)
            return True
        else:
            return False

    except Exception as e:
        logger.error(f"Error in rename_chat_file: {e}")
        return False


def fuzzy_search_chats(username: str, query: str) -> str:
    """Search through user's chats using fuzzy matching."""
    try:
        chats = get_user_chats_with_names(username)
        query_lower = query.lower()

        results = []
        for chat in chats:
            name = chat.get("name", "").lower()
            if query_lower in name:
                results.append(chat)

        if results:
            # Format results
            formatted_results = []
            for chat in results[:10]:  # Limit to 10 results
                formatted_results.append(f"- {chat['name']} (ID: {chat['chat_id']})")

            return f"Found {len(results)} matching chats:\n" + "\n".join(
                formatted_results
            )
        else:
            return f"No chats found matching '{query}'"

    except Exception as e:
        logger.error(f"Error in fuzzy_search_chats: {e}")
        return f"Error searching chats: {e}"


def render_all_chats(username: str) -> list:
    """Render all chats for a user in a formatted list."""
    try:
        chats = get_user_chats_with_names(username)

        formatted_chats = []
        for chat in chats:
            formatted_chats.append(
                {
                    "id": chat["chat_id"],
                    "name": chat["name"],
                    "created": chat["created_at"],
                    "display_name": f"{chat['name']} ({chat['chat_id']})",
                }
            )

        return formatted_chats

    except Exception as e:
        logger.error(f"Error in render_all_chats: {e}")
        return []
