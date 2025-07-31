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
from typing import Dict, Any, Tuple, Optional

from backend.consolidated_database import (
    get_consolidated_database,  # Corrected import
    InputSanitizer,
)

# Removed specific get_performance_database, get_llm_database, get_classifications_database
# as they are now accessed via the consolidated database object
from backend.timezone_utils import format_singapore_datetime
import logging

logger = logging.getLogger(__name__)


class StatsInterface:
    """
    Stats interface for user statistics.

    Initializes the StatsInterface instance.
    """

    def __init__(self):
        # All database access now goes through the consolidated database instance
        self.db = get_consolidated_database()
        self.sanitizer = InputSanitizer()

    def _generate_mermaid_flowchart(self, metrics: Dict[str, Any]) -> str:
        """Generates a Mermaid.js flowchart string from performance metrics."""
        flowchart_str = "graph TD\n"

        # Overall startup
        startup_time = metrics.get("app_startup", {}).get("avg_startup_time", 0)
        flowchart_str += f"A[App Startup] --> B(Avg: {startup_time:.2f}s)\n"

        # LLM Summary
        llm_summary = metrics.get("llm_performance_summary", [])
        if llm_summary:
            flowchart_str += "B --> C{LLM Performance}\n"
            for i, model in enumerate(llm_summary):
                model_name = model.get("model_name", "N/A")
                total_tokens = model.get("total_tokens", 0)
                avg_latency = (
                    model.get("avg_latency_ms", 0) / 1000
                )  # Convert to seconds
                flowchart_str += f"C --> C{i + 1}[{model_name} <br> Tokens: {total_tokens} <br> Latency: {avg_latency:.2f}s]\n"

        # API Calls
        api_summary = metrics.get("api_call_summary", [])
        if api_summary:
            flowchart_str += "B --> D{API Calls}\n"
            for i, api in enumerate(api_summary):
                endpoint = api.get("endpoint", "N/A")
                method = api.get("method", "N/A")
                total_calls = api.get("total_calls", 0)
                avg_duration = (
                    api.get("avg_duration_ms", 0) / 1000
                )  # Convert to seconds
                flowchart_str += f"D --> D{i + 1}[{endpoint} {method} <br> Calls: {total_calls} <br> Avg Duration: {avg_duration:.2f}s]\n"

        # Classifications
        classification_summary = metrics.get("classification_summary", [])
        if classification_summary:
            flowchart_str += "B --> E{File Classifications}\n"
            for i, classification in enumerate(classification_summary):
                result = classification.get("classification_result", "N/A")
                total_count = classification.get("total_count", 0)
                flowchart_str += f"E --> E{i + 1}[{result} <br> Count: {total_count}]\n"

        return flowchart_str

    def get_user_statistics(
        self, username: str
    ) -> Tuple[str, str, str, str, Optional[gr.File]]:
        """
        Retrieves comprehensive statistics for a given user.
        """
        if not username:
            return "Please log in to view statistics.", "{}", "", "", None

        sanitized_username = self.sanitizer.sanitize_username(username)
        stats: Dict[str, Any] = {"username": sanitized_username}

        try:
            # Fetch user-specific LLM performance
            llm_summary = self.db.get_llm_performance_summary(
                username=sanitized_username
            )
            stats["llm_performance_summary"] = llm_summary

            # Fetch user-specific API call performance
            api_summary = self.db.get_api_call_summary(username=sanitized_username)
            stats["api_call_summary"] = api_summary

            # Fetch chat statistics
            total_sessions_result = self.db.execute_query(
                "SELECT COUNT(*) FROM chat_sessions WHERE username = ?",
                (sanitized_username,),
            )
            total_messages_result = self.db.execute_query(
                "SELECT COUNT(*) FROM chat_messages WHERE username = ?",
                (sanitized_username,),
            )
            stats["chat_statistics"] = {
                "total_sessions": total_sessions_result[0][0]
                if total_sessions_result
                else 0,
                "total_messages": total_messages_result[0][0]
                if total_messages_result
                else 0,
            }

            # Fetch file classification statistics for the user
            classification_summary = self.db.get_document_classifications_by_user(
                username=sanitized_username
            )
            stats["classification_summary"] = classification_summary

            # Fetch overall app startup times (not user specific, but relevant to system health)
            app_startups = self.db.get_app_startup_records(
                limit=100
            )  # Get a good sample
            if app_startups:
                startup_times = [s["startup_time_seconds"] for s in app_startups]
                stats["app_startup"] = {
                    "total_startups": len(startup_times),
                    "avg_startup_time": sum(startup_times) / len(startup_times),
                    "min_startup_time": min(startup_times),
                    "max_startup_time": max(startup_times),
                }
            else:
                stats["app_startup"] = {
                    "total_startups": 0,
                    "avg_startup_time": 0.0,
                    "min_startup_time": 0.0,
                    "max_startup_time": 0.0,
                }

            # Generate Mermaid flowchart
            mermaid_chart = self._generate_mermaid_flowchart(stats)

            # Generate PDF report
            pdf_report_path = self._generate_pdf_report(username, stats)

            status_message = f"Statistics for {username} loaded successfully."
            return (
                status_message,
                json.dumps(stats, indent=2),
                mermaid_chart,
                self._format_stats_for_display(stats),
                gr.File(value=pdf_report_path, visible=True)
                if pdf_report_path
                else gr.File(visible=False),
            )
        except Exception as e:
            logger.error(f"Error retrieving statistics for {username}: {e}")
            return (
                f"Error retrieving statistics: {e}",
                "{}",
                "",
                f"Failed to load statistics: {e}",
                gr.File(visible=False),
            )

    def _format_stats_for_display(self, stats: Dict[str, Any]) -> str:
        """Formats the statistics into a human-readable string for Gradio Markdown."""
        display_text = "### User Statistics\n\n"

        display_text += f"**User:** {stats.get('username', 'N/A')}\n\n"

        # App Startup
        app_startup = stats.get("app_startup", {})
        display_text += "#### Application Startup\n"
        display_text += (
            f"- Total Startups Recorded: {app_startup.get('total_startups', 0)}\n"
        )
        display_text += (
            f"- Average Startup Time: {app_startup.get('avg_startup_time', 0):.2f}s\n"
        )
        display_text += (
            f"- Min Startup Time: {app_startup.get('min_startup_time', 0):.2f}s\n"
        )
        display_text += (
            f"- Max Startup Time: {app_startup.get('max_startup_time', 0):.2f}s\n\n"
        )

        # LLM Performance
        llm_summary = stats.get("llm_performance_summary", [])
        if llm_summary:
            display_text += "#### LLM Performance Summary\n"
            for model in llm_summary:
                display_text += (
                    f"- **Model:** {model.get('model_name', 'N/A')}\n"
                    f"  - Total Calls: {model.get('total_calls', 0)}\n"
                    f"  - Total Tokens (Prompt+Completion): {model.get('total_tokens', 0)}\n"
                    f"  - Average Latency: {model.get('avg_latency_ms', 0):.2f} ms\n"
                    f"  - Total Estimated Cost: ${model.get('total_cost', 0):.4f}\n"
                )
            display_text += "\n"
        else:
            display_text += (
                "#### LLM Performance Summary\n- No LLM performance data available.\n\n"
            )

        # API Call Performance
        api_summary = stats.get("api_call_summary", [])
        if api_summary:
            display_text += "#### API Call Performance Summary\n"
            for api_call in api_summary:
                display_text += (
                    f"- **Endpoint:** {api_call.get('endpoint', 'N/A')} ({api_call.get('method', 'N/A')})\n"
                    f"  - Total Calls: {api_call.get('total_calls', 0)}\n"
                    f"  - Average Duration: {api_call.get('avg_duration_ms', 0):.2f} ms\n"
                    f"  - Successful Calls: {api_call.get('successful_calls', 0)}\n"
                    f"  - Failed Calls: {api_call.get('failed_calls', 0)}\n"
                )
            display_text += "\n"
        else:
            display_text += "#### API Call Performance Summary\n- No API call performance data available.\n\n"

        # Chat Statistics
        chat_stats = stats.get("chat_statistics", {})
        display_text += "#### Chat Statistics\n"
        display_text += (
            f"- Total Chat Sessions: {chat_stats.get('total_sessions', 0)}\n"
        )
        display_text += f"- Total Messages: {chat_stats.get('total_messages', 0)}\n\n"

        # File Classification
        classification_summary = stats.get("classification_summary", [])
        if classification_summary:
            display_text += "#### Recent File Classifications\n"
            for classification in classification_summary:
                display_text += (
                    f"- **File:** {classification.get('file_path', 'N/A')}\n"
                    f"  - Result: {classification.get('classification_result', 'N/A')}\n"
                    f"  - Sensitivity: {classification.get('sensitivity_level', 'N/A')}\n"
                    f"  - Security: {classification.get('security_level', 'N/A')}\n"
                    f"  - Classified At: {format_singapore_datetime(classification.get('created_at', 'N/A'))}\n"
                )
            display_text += "\n"
        else:
            display_text += "#### Recent File Classifications\n- No file classification data available.\n\n"

        return display_text


def stats_interface(username_state, logged_in_state, debug_info_state):
    """
    Creates the Gradio Blocks interface for statistics, accepting external state variables.
    """
    stats_instance = StatsInterface()

    with gr.Blocks() as stats_block:
        gr.Markdown("## 📊 User & System Statistics")
        gr.Markdown(
            "View detailed performance metrics and usage statistics for the chatbot."
        )

        status_message = gr.Markdown("Please log in to view your statistics.")

        with gr.Tab("Summary Dashboard"):
            with gr.Row():
                with gr.Column():
                    gr.Markdown("### Performance Visualizations (Mermaid Flowchart)")
                    performance_visualizations = gr.Markdown(
                        "```mermaid\ngraph TD\n    A[Loading...]\n```",
                        elem_id="mermaid-chart",
                    )
                with gr.Column():
                    gr.Markdown("### Detailed Statistics")
                    statistics_tables = gr.Markdown(
                        "Statistics will appear here...",
                        elem_classes="scrollable-markdown",
                    )

            with gr.Row():
                raw_stats_json = gr.Json(
                    label="Raw Statistics JSON",
                    visible=False,
                    elem_classes="scrollable-json",
                )

            with gr.Row():
                with gr.Column():
                    refresh_stats_btn = gr.Button(
                        "🔄 Refresh Statistics",
                        size="lg",
                        elem_id="stats_refresh_btn",
                    )
                    pdf_report_file = gr.File(
                        label="Download PDF Report",
                        file_count="single",
                        elem_id="stats_pdf_report",
                        visible=False,
                    )

        # When the username_state changes, fetch user statistics
        username_state.change(
            fn=stats_instance.get_user_statistics,
            inputs=[username_state],
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

        # Allow manual refreshing of statistics
        refresh_stats_btn.click(
            fn=stats_instance.get_user_statistics,
            inputs=[username_state],
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

    return stats_block
