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
from typing import Dict, Any, Tuple, Optional

from backend.consolidated_database import (
    get_consolidated_database,
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
        self.db = get_consolidated_database()
        self.sanitizer = InputSanitizer()

    def _generate_mermaid_flowchart(self, metrics: Dict[str, Any]) -> str:
        mermaid_blocks = []
        # 1. Startup times (graph)
        if metrics.get("app_startup", {}).get("total_startups", 0) > 0:
            avg = metrics["app_startup"].get("avg_startup_time", 0)
            mermaid_blocks.append(
                f"graph TD\n    A[App Startup Times] --> B[Avg Startup: {avg:.2f}s]"
            )
        # 2. LLM summary (pie)
        llm_summary = metrics.get("llm_performance_summary", [])
        if llm_summary:
            pie_entries = []
            for model in llm_summary:
                name = model.get("model_name", "Unknown")
                count = model.get("total_calls", 0)
                pie_entries.append(f"{name} : {count}")
            if pie_entries:
                mermaid_blocks.append(
                    "pie title LLM Model Usage\n" + "\n".join(pie_entries)
                )
        # 3. API Calls (pie by endpoint-method)
        api_summary = metrics.get("api_call_summary", [])
        if api_summary:
            pie_entries = []
            for api in api_summary:
                endpoint = api.get("endpoint", "Unknown")
                method = api.get("method", "Unknown")
                count = api.get("total_calls", 0)
                pie_entries.append(f"{endpoint} {method} : {count}")
            if pie_entries:
                mermaid_blocks.append("pie title API Calls\n" + "\n".join(pie_entries))
        # 4. File classification (pie)
        classification_summary = metrics.get("classification_summary", [])
        if classification_summary:
            count = {}
            for c in classification_summary:
                label = str(c.get("classification_result", "Other"))
                count[label] = count.get(label, 0) + 1
            pie_lines = [f"{k} : {v}" for k, v in count.items()]
            if pie_lines:
                mermaid_blocks.append(
                    "pie title Classification Results\n" + "\n".join(pie_lines)
                )
        # 5. User stats: search queries and others (bar)
        user_stats = metrics.get("user_stats", {})
        if user_stats:
            bar_lines = []
            for k, v in user_stats.items():
                bar_lines.append(f"{k} : {v}")
            if bar_lines:
                mermaid_blocks.append("bar title User Stats\n" + "\n".join(bar_lines))
        # Return them separated
        return "\n\n".join([f"```mermaid\n{b}\n```" for b in mermaid_blocks])

    def get_user_statistics(
        self, username: str
    ) -> Tuple[str, str, str, Optional[gr.File]]:
        """
        Retrieves comprehensive statistics for a given user.
        Always returns _some_ content (never blank).
        """
        if not username:
            return (
                "Please log in to view statistics.",
                "",
                "Please log in.",
                None,
            )

        from sqlite3 import OperationalError

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
                "SELECT COUNT(*) FROM chat_messages WHERE session_id IN (SELECT session_id FROM chat_sessions WHERE username = ?)",
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

            # Fetch overall app startup times (not user specific)
            app_startups = self.db.get_app_startup_records(limit=100)
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

            # Safer uploaded_files and audio_files with fallback; returns (count, avg_size)
            def _safe_stat_query(sql, params, default):
                try:
                    rows = self.db.execute_query(sql, params)
                    if rows and len(rows[0]) > 1:
                        return rows[0][0], float(rows[0][1]) if rows[0][
                            1
                        ] is not None else 0.0
                    elif rows:
                        return rows[0][0], 0.0
                    return default
                except OperationalError as oe:  # Table missing
                    logger.warning(
                        f"[StatsInterface] Table missing for query {sql}: {oe}"
                    )
                    return default
                except Exception:
                    return default

            total_uploaded_files, avg_uploaded_file_size = _safe_stat_query(
                "SELECT COUNT(*), COALESCE(AVG(file_size),0) FROM uploaded_files WHERE username = ?",
                (sanitized_username,),
                (0, 0.0),
            )
            total_audio_files, avg_audio_file_size = _safe_stat_query(
                "SELECT COUNT(*), COALESCE(AVG(file_size),0) FROM uploaded_files WHERE username = ? AND file_type LIKE 'audio/%'",
                (sanitized_username,),
                (0, 0.0),
            )

            stats["files_uploaded"] = {
                "total_files": total_uploaded_files,
                "avg_file_size": avg_uploaded_file_size,
            }
            stats["audio_files_uploaded"] = {
                "total_audio_files": total_audio_files,
                "avg_audio_file_size": avg_audio_file_size,
            }

            # Fetch user stats (e.g. search queries)
            stats["user_stats"] = self.db.get_all_user_stats(sanitized_username)

            from backend.markdown_formatter import format_markdown

            raw_mermaid_chart = self._generate_mermaid_flowchart(stats)
            mermaid_chart = format_markdown(raw_mermaid_chart)
            # Fallback: If mermaid_chart is empty or only whitespace, show a message
            if not mermaid_chart.strip():
                mermaid_chart = "No diagram data available."

            try:
                pdf_report_path = self.db.generate_pdf_report(sanitized_username, stats)
            except Exception as pdf_exc:
                logger.error(f"PDF generation failed: {pdf_exc}")
                pdf_report_path = None

            status_message = f"Statistics for {username} loaded successfully."

            # Only return status_md, mermaid_md, pretty_stats_md, file
            return (
                status_message,  # markdown
                mermaid_chart,  # markdown
                self._format_stats_for_display(stats),  # markdown
                gr.File(value=pdf_report_path, visible=True)
                if pdf_report_path
                else gr.File(visible=False),  # file
            )
        except Exception as e:
            logger.error(f"Error retrieving statistics for {username}: {e}")

            return (
                f"Error retrieving statistics: {e}",  # markdown
                "",
                f"Failed to load statistics: {e}",
                gr.File(visible=False),
            )

    def _format_stats_for_display(self, stats: Dict[str, Any]) -> str:
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

        # File Upload & Audio Statistics
        files_uploaded = stats.get("files_uploaded", {})
        audio_files_uploaded = stats.get("audio_files_uploaded", {})
        display_text += "#### File Upload Statistics\n"
        display_text += (
            f"- Total Files Uploaded: {files_uploaded.get('total_files', 0)}\n"
            f"- Average File Size: {files_uploaded.get('avg_file_size', 0):.1f} bytes\n"
            f"- Total Audio Files Uploaded: {audio_files_uploaded.get('total_audio_files', 0)}\n"
            f"- Average Audio File Size: {audio_files_uploaded.get('avg_audio_file_size', 0):.1f} bytes\n\n"
        )

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

        # User Stats (Custom)
        user_stats = stats.get("user_stats", {})
        if user_stats and any(user_stats.values()):
            display_text += "#### Custom User Statistics\n"
            for key, val in user_stats.items():
                display_text += f"- {key.replace('_', ' ').title()}: {val}\n"
            display_text += "\n"

        return display_text
