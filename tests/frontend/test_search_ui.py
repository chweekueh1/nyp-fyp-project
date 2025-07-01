#!/usr/bin/env python3
import gradio as gr
import sys
from pathlib import Path

# Add parent directory to path for imports
parent_dir = Path(__file__).parent.parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Import backend functions directly
from backend import search_chat_history


async def handle_search(query, username):
    print(f"Search query: {query} for user {username}")
    try:
        if not query or not query.strip():
            return "❌ Please enter a search query"
        result = search_chat_history(query, username)
        print(f"Backend search result: {result}")
        if result and len(result) > 0:
            return f"✅ Search results: {result}"
        else:
            return "🔍 No matching chats found"
    except Exception as e:
        print(f"Search error: {e}")
        return f"❌ Search error: {str(e)}"


async def handle_show_all_chats(username):
    print(f"Show all chats for user {username}")
    try:
        # This is a placeholder; implement as needed or remove button if not needed
        return "📝 No chats found"
    except Exception as e:
        print(f"Show all chats error: {e}")
        return f"❌ Show all chats error: {str(e)}"


def test_search_interface():
    """Test the search interface with all features."""
    with gr.Blocks(title="Search Interface Test") as app:
        # Initialize states
        gr.State(True)  # Start logged in for testing
        username_state = gr.State("test")
        gr.State("test_chat_id")
        gr.State([])

        # Header
        gr.Markdown("# Search Interface Test")

        # Search inputs
        search_query = gr.Textbox(
            label="Search Query", placeholder="Enter search term..."
        )
        search_button = gr.Button("Search", variant="primary")
        show_all_button = gr.Button("Show All Chats", variant="secondary")

        # Output
        search_results = gr.Markdown("Search results will appear here...")

        # Add a search box with elem_id for Ctrl+K
        gr.Textbox(label="Search", elem_id="search_box", visible=True)
        gr.HTML("""
        <script>
        document.addEventListener('keydown', function(e) {
            if (e.ctrlKey && e.key === 'k') {
                e.preventDefault();
                var search = document.querySelector('input#search_box');
                if (search) { search.focus(); }
            }
        });
        </script>
        """)

        # Event handlers
        search_button.click(
            fn=handle_search,
            inputs=[search_query, username_state],
            outputs=[search_results],
            api_name="search",
        )

        show_all_button.click(
            fn=handle_show_all_chats,
            inputs=[username_state],
            outputs=[search_results],
            api_name="show_all_chats",
        )

        # Status display
        gr.Markdown("## Test Instructions")
        gr.Markdown("""
        **Test the following:**
        1. **Search Query:** Enter a search term and click Search
        2. **Fuzzy Search:** Try the fuzzy search functionality
        3. **Show All Chats:** Click to display all chats
        4. **Search Results:** Results should be displayed

        **Expected Behavior:**
        - Search button should be responsive
        - Backend search functions should be called directly
        - Search results should be displayed
        - Show all chats should work
        - Error messages should show for invalid inputs
        """)

    return app


def test_chat_history_interface():
    """Test the chat history interface."""

    async def handle_chat_search(query, username):
        """Handle chat history search using backend function directly."""
        print(f"Chat history search: {query} for user {username}")
        try:
            if not query or not query.strip():
                return "❌ Please enter a search query"

            # Call backend function directly
            result = search_chat_history(query, username)
            print(f"Backend chat history search result: {result}")

            if result and len(result) > 0:
                # result is a list of dictionaries with 'chat_id', 'message', 'timestamp' keys
                history_list = "\n".join(
                    [
                        f"- Chat {item['chat_id']}: {item['message'][:50]}..."
                        for item in result[:5]
                    ]
                )  # Show first 5 results
                return f"✅ Chat history search results:\n{history_list}"
            else:
                return "🔍 No matching chat history found"
        except Exception as e:
            print(f"Chat history search error: {e}")
            return f"❌ Chat history search error: {str(e)}"

    with gr.Blocks(title="Chat History Interface Test") as app:
        # Initialize states
        gr.State(True)
        username_state = gr.State("test")
        gr.State("test_chat_id")
        gr.State([])

        # Header
        gr.Markdown("# Chat History Interface Test")

        # Search inputs
        history_search_query = gr.Textbox(
            label="Search Chat History", placeholder="Enter search term..."
        )
        history_search_button = gr.Button("Search History", variant="primary")

        # Output
        history_results = gr.Markdown("Chat history search results will appear here...")

        # Event handler
        history_search_button.click(
            fn=handle_chat_search,
            inputs=[history_search_query, username_state],
            outputs=[history_results],
            api_name="search_history",
        )

        # Status display
        gr.Markdown("## Test Instructions")
        gr.Markdown("""
        **Test the following:**
        1. **Search History:** Enter a search term and click Search History
        2. **History Results:** Search results should be displayed
        3. **Error Handling:** Try searching with empty queries

        **Expected Behavior:**
        - Search History button should be responsive
        - Backend search function should be called directly
        - Search results should be displayed
        - Error messages should show for invalid inputs
        """)

    return app


if __name__ == "__main__":
    app = test_search_interface()
    # Use Docker-compatible launch configuration
    launch_config = {
        "debug": True,
        "share": False,
        "inbrowser": False,
        "quiet": False,
        "show_error": True,
        "server_name": "0.0.0.0",  # Listen on all interfaces for Docker
        "server_port": 7860,  # Use the same port as main app
    }
    print(
        f"🌐 Launching search test app on {launch_config['server_name']}:{launch_config['server_port']}"
    )
    app.launch(**launch_config)
