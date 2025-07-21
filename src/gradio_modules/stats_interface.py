# stats_interface.py
#!/usr/bin/env python3
"""
Stats Interface module for the NYP FYP CNC Chatbot.

This module provides a comprehensive statistics interface including:

- User performance analytics dashboard
- Docker build time statistics
- API call performance metrics
- App startup time tracking
- LLM usage statistics
- File classification metrics
- Audio transcription statistics
- Mermaid.js diagram rendering
- PDF export functionality
- Real-time data visualization

The interface integrates with the consolidated SQLite database system
and provides detailed performance insights for each user.
"""

import gradio as gr
import json
import os
import tempfile
from typing import Dict, Any, Tuple, Optional
from datetime import datetime

from backend.consolidated_database import (
    get_user_database,
    get_performance_database,
    get_llm_database,
    get_chat_database,
    get_classifications_database,
    InputSanitizer,
)
from backend.timezone_utils import format_singapore_datetime
import logging

logger = logging.getLogger(__name__)


class StatsInterface:
    """
    Stats interface for user statistics.

    Initializes the StatsInterface instance.
    """

    def __init__(self):
        self.user_db = get_user_database()
        self.perf_db = get_performance_database()
        self.llm_db = get_llm_database()
        self.chat_db = get_chat_database()
        self.class_db = get_classifications_database()
        self.sanitizer = InputSanitizer()

    def get_user_statistics(
        self, username: str
    ) -> Tuple[gr.Markdown, gr.Json, gr.HTML, gr.HTML, gr.File]:
        """
        Retrieves and formats statistics for a given user.
        Returns a tuple of Gradio component updates.
        """
        if not username:
            logger.info("No username provided. Skipping statistics retrieval.")
            # Return empty/disabled states for all outputs
            return (
                gr.update(
                    value="""
                    ## 📊 User Statistics
                    Please log in to view your personalized statistics.
                    """,
                    visible=True,
                ),  # status_message
                gr.update(value={}, visible=False),  # raw_stats_json
                gr.update(value="", visible=False),  # performance_visualizations
                gr.update(value="", visible=False),  # statistics_tables
                gr.update(value=None, visible=False),  # pdf_report_file
            )

        logger.info(f"Retrieving statistics for user: {username}")
        try:
            user_data = self.user_db.get_user(username)
            if not user_data:
                logger.warning(f"User '{username}' not found in database.")
                return (
                    f"Error: User '{username}' not found. Please log in again.",
                    "{}",
                    gr.Markdown(""),
                    gr.HTML(""),
                    gr.File(visible=False),
                )
            user_id = user_data["id"]
            if not user_id:
                logger.warning(f"User '{username}' not found in database.")
                return (
                    gr.update(
                        value=f"""
                        ## 📊 User Statistics
                        User **{username}** not found. Please ensure you are logged in correctly.
                        """,
                        visible=True,
                    ),
                    gr.update(value={}),
                    gr.update(value="", visible=False),
                    gr.update(value="", visible=False),
                    gr.update(value=None, visible=False),
                )

            # Get data from various databases
            chat_stats = self.chat_db.get_user_chat_summary(user_id)
            classification_stats = self.class_db.get_user_classification_summary(
                user_id
            )
            llm_stats = self.llm_db.get_user_llm_summary(user_id)
            app_usage_stats = self.perf_db.get_user_app_usage_summary(user_id)
            file_upload_stats = self.perf_db.get_user_file_upload_summary(user_id)
            audio_transcription_stats = (
                self.perf_db.get_user_audio_transcription_summary(user_id)
            )

            # Aggregate all statistics
            all_stats = {
                "user_id": user_id,
                "username": username,
                "chat_statistics": chat_stats,
                "classification_statistics": classification_stats,
                "llm_statistics": llm_stats,
                "app_usage_statistics": app_usage_stats,
                "file_upload_statistics": file_upload_stats,
                "audio_transcription_statistics": audio_transcription_stats,
                "generation_time": datetime.now().isoformat(),
            }

            # Generate formatted tables
            tables_html = self._format_statistics_tables(all_stats)

            # Generate visualizations (Mermaid.js diagrams)
            mermaid_html = self._generate_performance_visualizations(all_stats)

            # Generate PDF report (placeholder/simplified)
            pdf_path = self._generate_pdf_report(all_stats, username)

            status_msg = f"""
            ## 📊 User Statistics for {username}
            Last updated: {format_singapore_datetime(datetime.now().isoformat())}
            """

            return (
                gr.update(value=status_msg, visible=True),
                gr.update(value=all_stats, visible=True),
                gr.update(value=mermaid_html, visible=True),
                gr.update(value=tables_html, visible=True),
                gr.update(value=pdf_path, visible=True if pdf_path else False),
            )

        except Exception as e:
            logger.error(
                f"Error retrieving statistics for user {username}: {e}", exc_info=True
            )
            return (
                gr.update(
                    value=f"Error retrieving statistics: {e}. Please try again later.",
                    visible=True,
                ),
                gr.update(value={}, visible=False),
                gr.update(value="", visible=False),
                gr.update(value="", visible=False),
                gr.update(value=None, visible=False),
            )

    def _format_statistics_tables(self, stats: Dict[str, Any]) -> str:
        """Formats various statistics into HTML tables."""
        html_output = "<h3>Detailed Statistics</h3>"

        # Chat Statistics
        chat_data = stats.get("chat_statistics", {})
        html_output += "<h4>Chat Statistics</h4>"
        if chat_data:
            html_output += f"""
            <table>
                <tr><th>Total Chats</th><td>{chat_data.get("total_chats", 0)}</td></tr>
                <tr><th>Total Messages</th><td>{chat_data.get("total_messages", 0)}</td></tr>
                <tr><th>Avg. Messages per Chat</th><td>{chat_data.get("avg_messages_per_chat", 0):.2f}</td></tr>
                <tr><th>Last Chat Date</th><td>{format_singapore_datetime(chat_data.get("last_chat_date")) if chat_data.get("last_chat_date") else "N/A"}</td></tr>
            </table>
            """
        else:
            html_output += "<p>No chat data available.</p>"

        # LLM Usage Statistics
        llm_data = stats.get("llm_statistics", {})
        html_output += "<h4>LLM Usage Statistics</h4>"
        if llm_data:
            html_output += f"""
            <table>
                <tr><th>Total LLM Calls</th><td>{llm_data.get("total_llm_calls", 0)}</td></tr>
                <tr><th>Total Tokens Used</th><td>{llm_data.get("total_tokens_used", 0)}</td></tr>
                <tr><th>Avg. Response Time (s)</th><td>{llm_data.get("avg_response_time", 0):.2f}</td></tr>
            </table>
            """
        else:
            html_output += "<p>No LLM usage data available.</p>"

        # Classification Statistics
        classification_data = stats.get("classification_statistics", {})
        html_output += "<h4>File Classification Statistics</h4>"
        if classification_data:
            html_output += f"""
            <table>
                <tr><th>Total Files Classified</th><td>{classification_data.get("total_files_classified", 0)}</td></tr>
                <tr><th>Last Classification Date</th><td>{format_singapore_datetime(classification_data.get("last_classification_date")) if classification_data.get("last_classification_date") else "N/A"}</td></tr>
                <tr><th>Avg. Classification Time (s)</th><td>{classification_data.get("avg_classification_time", 0):.2f}</td></tr>
            </table>
            """
        else:
            html_output += "<p>No file classification data available.</p>"

        # File Upload Statistics
        file_upload_data = stats.get("file_upload_statistics", {})
        html_output += "<h4>File Upload Statistics</h4>"
        if file_upload_data:
            html_output += f"""
            <table>
                <tr><th>Total Files Uploaded</th><td>{file_upload_data.get("total_files_uploaded", 0)}</td></tr>
                <tr><th>Last Upload Date</th><td>{format_singapore_datetime(file_upload_data.get("last_upload_date")) if file_upload_data.get("last_upload_date") else "N/A"}</td></tr>
            </table>
            """
        else:
            html_output += "<p>No file upload data available.</p>"

        # Audio Transcription Statistics
        audio_transcription_data = stats.get("audio_transcription_statistics", {})
        html_output += "<h4>Audio Transcription Statistics</h4>"
        if audio_transcription_data:
            html_output += f"""
            <table>
                <tr><th>Total Transcriptions</th><td>{audio_transcription_data.get("total_transcriptions", 0)}</td></tr>
                <tr><th>Last Transcription Date</th><td>{format_singapore_datetime(audio_transcription_data.get("last_transcription_date")) if audio_transcription_data.get("last_transcription_date") else "N/A"}</td></tr>
            </table>
            """
        else:
            html_output += "<p>No audio transcription data available.</p>"

        return html_output

    def _generate_performance_visualizations(self, stats: Dict[str, Any]) -> str:
        """Generates Mermaid.js diagrams for performance visualizations."""
        # Example: Simple Mermaid graph for total calls
        llm_calls = stats.get("llm_statistics", {}).get("total_llm_calls", 0)
        chat_messages = stats.get("chat_statistics", {}).get("total_messages", 0)
        files_classified = stats.get("classification_statistics", {}).get(
            "total_files_classified", 0
        )

        mermaid_code = f"""
        graph TD
            A[User Activity] --> B{{Total Interactions}}
            B --> C(LLM Calls: {llm_calls})
            B --> D(Chat Messages: {chat_messages})
            B --> E(Files Classified: {files_classified})
        """
        html = f"""
        <h3>Activity Flow</h3>
        <pre class="mermaid">
        {mermaid_code}
        </pre>
        <script type="module">
            import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.js';
            mermaid.initialize({{ startOnLoad: true }});
        </script>
        """
        return html

    def _generate_pdf_report(
        self, stats: Dict[str, Any], username: str
    ) -> Optional[str]:
        """
        Generates a simplified mock PDF report.
        In a real application, this would use a library like ReportLab or FPDF.
        """
        try:
            temp_dir = tempfile.mkdtemp()
            pdf_path = os.path.join(
                temp_dir, f"{username}_stats_report.txt"
            )  # Using .txt for mock
            with open(pdf_path, "w") as f:
                f.write("NYP FYP Chatbot - User Statistics Report\n\n")
                f.write(f"Report for: {username}\n")
                f.write(
                    f"Generated on: {format_singapore_datetime(datetime.now().isoformat())}\n\n"
                )
                f.write("--- Raw Statistics ---\n")
                f.write(json.dumps(stats, indent=2))
                f.write("\n\n--- End of Report ---\n")
            logger.info(f"Mock PDF report generated at: {pdf_path}")
            return pdf_path
        except Exception as e:
            logger.error(f"Error generating mock PDF report: {e}", exc_info=True)
            return None


stats_instance = StatsInterface()


def create_stats_interface(
    username_state: gr.State, logged_in_state: gr.State, debug_info_state: gr.State
) -> gr.Blocks:
    """
    Creates the Gradio Blocks for the statistics interface.

    :param username_state: Gradio State for the current username.
    :type username_state: gr.State
    :param logged_in_state: Gradio State for the login status.
    :type logged_in_state: gr.State
    :param debug_info_state: Gradio State for displaying debug information.
    :type debug_info_state: gr.State
    :return: The Blocks object containing the statistics UI.
    :rtype: gr.Blocks
    """
    with gr.Blocks() as stats_block:
        gr.Markdown("## 📊 User Statistics & Analytics")
        gr.Markdown(
            "View your chatbot usage, performance metrics, and activity trends."
        )

        # Display area for status messages (e.g., "loading", "error", "no data")
        status_message = gr.Markdown(value="Loading statistics...", visible=True)

        with gr.Row():
            with gr.Column(scale=2):
                with gr.Group(elem_id="statistics_display_group"):
                    performance_visualizations = gr.HTML(
                        value="<p>Visualizations will appear here.</p>",
                        elem_id="performance_visualizations",
                        visible=False,
                    )
                    statistics_tables = gr.HTML(
                        value="<p>Detailed tables will appear here.</p>",
                        elem_id="statistics_tables",
                        visible=False,
                    )
                    raw_stats_json = gr.Json(
                        value={}, label="Raw Statistics (JSON)", visible=False
                    )
            with gr.Column(scale=1):
                with gr.Group(elem_id="stats_actions_group"):
                    refresh_stats_btn = gr.Button(
                        "🔄 Refresh Statistics",
                        variant="primary",
                        size="lg",
                        elem_id="stats_refresh_btn",
                    )
                    pdf_report_file = gr.File(
                        label="Download PDF Report",
                        file_count="single",
                        elem_id="stats_pdf_report",
                        visible=False,
                    )

        # Wire event to username_state.change
        # This will trigger when a user logs in (username_state changes from "" to actual username)
        # And when a user logs out (username_state changes from actual username to "")
        username_state.change(
            fn=stats_instance.get_user_statistics,
            inputs=[username_state],  # Pass the username_state
            outputs=[
                status_message,
                raw_stats_json,
                performance_visualizations,
                statistics_tables,
                pdf_report_file,
            ],
            queue=True,
            show_progress="full",
        )

        refresh_stats_btn.click(
            fn=stats_instance.get_user_statistics,
            inputs=[username_state],  # Pass the username_state
            outputs=[
                status_message,
                raw_stats_json,
                performance_visualizations,
                statistics_tables,
                pdf_report_file,
            ],
            queue=True,
            show_progress="full",
        )

    return stats_block  # Return the entire Blocks object
