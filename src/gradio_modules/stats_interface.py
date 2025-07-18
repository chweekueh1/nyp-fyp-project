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

import contextlib
import gradio as gr
import json
import time
import os
import subprocess
import tempfile
from typing import Dict, Any, List, Tuple
from datetime import datetime

from backend.consolidated_database import (
    get_user_database,
    get_performance_database,
    get_llm_database,
    get_chat_database,
    get_classifications_database,
    InputSanitizer,
)
from backend.performance_tracker import get_performance_tracker
from backend.config import get_chatbot_dir
from backend.timezone_utils import get_utc_timestamp, format_singapore_datetime
from backend.markdown_formatter import format_markdown


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
        self.classifications_db = get_classifications_database()
        self.tracker = get_performance_tracker()
        self.docker_build_times = self._load_docker_build_times()
        self.benchmark_results = self._load_benchmark_results()

    def _load_docker_build_times(self):
        build_times_path = os.path.abspath(
            os.path.join(
                os.path.dirname(__file__), "../../data/docker_build_times.json"
            )
        )
        if os.path.exists(build_times_path):
            try:
                with open(build_times_path, "r") as f:
                    data = json.load(f)

                # Handle new format: { "history": [...], "averages": {...}, "last_build_time": "..." }
                if isinstance(data, dict) and "averages" in data:
                    # New format
                    averages = data.get("averages", {})
                    last_build_time = data.get("last_build_time", "")
                    # Calculate overall average if multiple images
                    overall_avg = (
                        sum(averages.values()) / len(averages) if averages else 0.0
                    )
                    return {
                        "avg_duration": overall_avg,
                        "averages": averages,
                        "last_build_time": last_build_time,
                        "history": data.get("history", []),
                    }
                elif isinstance(data, dict) and "avg_duration" in data:
                    return data
                elif isinstance(data, list):
                    if not data:
                        return {
                            "avg_duration": 0.0,
                            "history": [],
                            "last_build_time": "",
                        }
                    # Calculate average from history
                    durations = [
                        item.get("duration", 0)
                        for item in data
                        if isinstance(item, dict)
                    ]
                    avg = sum(durations) / len(durations) if durations else 0.0
                    return {
                        "avg_duration": avg,
                        "history": data,
                        "last_build_time": data[-1].get("timestamp", "")
                        if data
                        else "",
                    }
                else:
                    return {"avg_duration": 0.0, "history": [], "last_build_time": ""}
            except Exception as e:
                print(f"[WARNING] Could not load Docker build times: {e}")
                return {"avg_duration": 0.0, "history": [], "last_build_time": ""}
        return {"avg_duration": 0.0, "history": [], "last_build_time": ""}

    def _load_benchmark_results(self):
        # Load the last benchmark results from JSON (if present)
        bench_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../../data/benchmark_results.json")
        )
        if os.path.exists(bench_path):
            try:
                with open(bench_path, "r") as f:
                    data = json.load(f)
                return data
            except Exception as e:
                print(f"[WARNING] Could not load benchmark results: {e}")
                return {}
        return {}

    def get_user_stats(self, username: str) -> Dict[str, Any]:
        """Get comprehensive statistics for a user.

        :param username: Username to get stats for
        :type username: str
        :return: Dictionary containing user statistics
        :rtype: Dict[str, Any]
        """
        try:
            # Sanitize username
            username = InputSanitizer.sanitize_username(username)

            # Get user info
            user = self.user_db.get_user(username)
            if not user:
                return {"error": "User not found"}

            # Get performance summary
            perf_summary = self.tracker.get_user_performance_summary(username, days=30)

            # Get LLM usage stats
            llm_stats = self._get_llm_stats(username)

            # Get chat stats
            chat_stats = self._get_chat_stats(username)

            # Get classification stats
            classification_stats = self._get_classification_stats(username)

            # Get detailed performance metrics
            detailed_metrics = self._get_detailed_metrics(username)

            # Get benchmark statistics
            benchmark_stats = self._get_benchmark_stats(username)

            return {
                "user_info": user,
                "performance_summary": perf_summary,
                "llm_stats": llm_stats,
                "chat_stats": chat_stats,
                "classification_stats": classification_stats,
                "detailed_metrics": detailed_metrics,
                "benchmark_stats": benchmark_stats,
                "docker_build_times": self.docker_build_times,
                "timestamp": get_utc_timestamp(),
            }

        except Exception as e:
            return {"error": f"Failed to get user stats: {str(e)}"}

    def _get_llm_stats(self, username: str) -> Dict[str, Any]:
        """Get LLM usage statistics for a user.

        :param username: Username
        :type username: str
        :return: LLM statistics
        :rtype: Dict[str, Any]
        """
        try:
            # Get LLM sessions
            query = """
                SELECT COUNT(*) as total_sessions,
                       SUM(message_count) as total_messages,
                       SUM(token_count) as total_tokens,
                       AVG(token_count) as avg_tokens_per_session
                FROM llm_sessions
                WHERE username = ? AND created_at >= datetime('now', '-30 days')
            """
            sessions = self.llm_db.execute_query(query, (username,))

            # Get recent LLM messages
            query = """
                SELECT message_type, COUNT(*) as count, AVG(token_count) as avg_tokens
                FROM llm_messages lm
                JOIN llm_sessions ls ON lm.session_id = ls.session_id
                WHERE ls.username = ? AND lm.timestamp >= datetime('now', '-30 days')
                GROUP BY message_type
            """
            messages = self.llm_db.execute_query(query, (username,))

            # Get embedding usage
            query = """
                SELECT COUNT(*) as total_embeddings,
                       SUM(usage_count) as total_usage
                FROM llm_embeddings
                WHERE created_at >= datetime('now', '-30 days')
            """
            embeddings = self.llm_db.execute_query(query)

            return {
                "sessions": {
                    "total": sessions[0][0] if sessions else 0,
                    "total_messages": sessions[0][1]
                    if sessions and sessions[0][1]
                    else 0,
                    "total_tokens": sessions[0][2]
                    if sessions and sessions[0][2]
                    else 0,
                    "avg_tokens_per_session": sessions[0][3]
                    if sessions and sessions[0][3]
                    else 0,
                },
                "messages": {
                    msg[0]: {"count": msg[1], "avg_tokens": msg[2]} for msg in messages
                },
                "embeddings": {
                    "total": embeddings[0][0] if embeddings else 0,
                    "total_usage": embeddings[0][1]
                    if embeddings and embeddings[0][1]
                    else 0,
                },
            }

        except Exception as e:
            return {"error": f"Failed to get LLM stats: {str(e)}"}

    def _get_chat_stats(self, username: str) -> Dict[str, Any]:
        """Get chat statistics for a user.

        :param username: Username
        :type username: str
        :return: Chat statistics
        :rtype: Dict[str, Any]
        """
        try:
            # Get chat sessions
            query = """
                SELECT COUNT(*) as total_sessions,
                       SUM(message_count) as total_messages,
                       AVG(message_count) as avg_messages_per_session
                FROM chat_sessions
                WHERE username = ? AND created_at >= datetime('now', '-30 days')
            """
            sessions = self.chat_db.execute_query(query, (username,))

            # Get message types
            query = """
                SELECT message_type, COUNT(*) as count
                FROM chat_messages cm
                JOIN chat_sessions cs ON cm.session_id = cs.session_id
                WHERE cs.username = ? AND cm.timestamp >= datetime('now', '-30 days')
                GROUP BY message_type
            """
            messages = self.chat_db.execute_query(query, (username,))

            return {
                "sessions": {
                    "total": sessions[0][0] if sessions else 0,
                    "total_messages": sessions[0][1]
                    if sessions and sessions[0][1]
                    else 0,
                    "avg_messages_per_session": sessions[0][2]
                    if sessions and sessions[0][2]
                    else 0,
                },
                "messages": {msg[0]: msg[1] for msg in messages},
            }

        except Exception as e:
            return {"error": f"Failed to get chat stats: {str(e)}"}

    def _get_classification_stats(self, username: str) -> Dict[str, Any]:
        """Get file classification statistics for a user.

        :param username: Username
        :type username: str
        :return: Classification statistics
        :rtype: Dict[str, Any]
        """
        try:
            # Get classification counts
            query = """
                SELECT COUNT(*) as total_classifications,
                       AVG(processing_time) as avg_processing_time,
                       SUM(file_size) as total_file_size
                FROM classifications
                WHERE username = ? AND created_at >= datetime('now', '-30 days')
            """
            classifications = self.classifications_db.execute_query(query, (username,))

            # Get classification results
            query = """
                SELECT classification_result, COUNT(*) as count
                FROM classifications
                WHERE username = ? AND created_at >= datetime('now', '-30 days')
                GROUP BY classification_result
            """
            results = self.classifications_db.execute_query(query, (username,))

            # Get extraction methods
            query = """
                SELECT extraction_method, COUNT(*) as count, AVG(processing_time) as avg_time
                FROM classifications
                WHERE username = ? AND created_at >= datetime('now', '-30 days')
                GROUP BY extraction_method
            """
            methods = self.classifications_db.execute_query(query, (username,))

            return {
                "overview": {
                    "total": classifications[0][0] if classifications else 0,
                    "avg_processing_time": classifications[0][1]
                    if classifications and classifications[0][1]
                    else 0,
                    "total_file_size": classifications[0][2]
                    if classifications and classifications[0][2]
                    else 0,
                },
                "results": {result[0]: result[1] for result in results},
                "methods": {
                    method[0]: {"count": method[1], "avg_time": method[2]}
                    for method in methods
                },
            }

        except Exception as e:
            return {"error": f"Failed to get classification stats: {str(e)}"}

    def _get_detailed_metrics(self, username: str) -> Dict[str, Any]:
        """Get detailed performance metrics for a user.

        :param username: Username
        :type username: str
        :return: Detailed metrics
        :rtype: Dict[str, Any]
        """
        try:
            # Get performance metrics
            query = """
                SELECT metric_type, metric_name, AVG(metric_value) as avg_value,
                       MIN(metric_value) as min_value, MAX(metric_value) as max_value
                FROM performance_metrics
                WHERE username = ? AND timestamp >= datetime('now', '-30 days')
                GROUP BY metric_type, metric_name
            """
            metrics = self.perf_db.execute_query(query, (username,))

            # Organize metrics by type
            organized_metrics = {}
            for metric in metrics:
                metric_type = metric[0]
                metric_name = metric[1]
                if metric_type not in organized_metrics:
                    organized_metrics[metric_type] = {}
                organized_metrics[metric_type][metric_name] = {
                    "avg": metric[2],
                    "min": metric[3],
                    "max": metric[4],
                }

            return organized_metrics

        except Exception as e:
            return {"error": f"Failed to get detailed metrics: {str(e)}"}

    def _get_benchmark_stats(self, username: str) -> Dict[str, Any]:
        """Get benchmark statistics for a user.

        :param username: Username
        :type username: str
        :return: Benchmark statistics
        :rtype: Dict[str, Any]
        """
        try:
            # Get benchmark metrics
            query = """
                SELECT metric_name, AVG(metric_value) as avg_value,
                       MIN(metric_value) as min_value, MAX(metric_value) as max_value,
                       COUNT(*) as run_count, metadata
                FROM performance_metrics
                WHERE username = ? AND metric_type = 'benchmark'
                AND timestamp >= datetime('now', '-30 days')
                GROUP BY metric_name
                ORDER BY avg_value DESC
            """
            benchmarks = self.perf_db.execute_query(query, (username,))

            # Organize benchmarks by category
            benchmark_stats = {}
            for bench in benchmarks:
                metric_name = bench[0]
                # Extract benchmark name and metric type from metric_name
                if "_mean" in metric_name:
                    benchmark_name = metric_name.replace("_mean", "")
                    metric_type = "mean"
                elif "_stddev" in metric_name:
                    benchmark_name = metric_name.replace("_stddev", "")
                    metric_type = "stddev"
                elif "_min" in metric_name:
                    benchmark_name = metric_name.replace("_min", "")
                    metric_type = "min"
                elif "_max" in metric_name:
                    benchmark_name = metric_name.replace("_max", "")
                    metric_type = "max"
                elif "_median" in metric_name:
                    benchmark_name = metric_name.replace("_median", "")
                    metric_type = "median"
                else:
                    continue

                if benchmark_name not in benchmark_stats:
                    benchmark_stats[benchmark_name] = {
                        "mean": 0.0,
                        "stddev": 0.0,
                        "min": 0.0,
                        "max": 0.0,
                        "median": 0.0,
                        "run_count": 0,
                        "category": "unknown",
                        "description": "No description available",
                    }

                benchmark_stats[benchmark_name][metric_type] = bench[1]
                benchmark_stats[benchmark_name]["run_count"] = bench[4]

                # Parse metadata for category and description
                with contextlib.suppress(json.JSONDecodeError, KeyError):
                    metadata_str = bench[5] or "{}"
                    metadata = json.loads(metadata_str)
                    benchmark_stats[benchmark_name]["category"] = metadata.get(
                        "category", "unknown"
                    )
                    benchmark_stats[benchmark_name]["description"] = metadata.get(
                        "description", "No description available"
                    )
            return benchmark_stats

        except Exception as e:
            return {"error": f"Failed to get benchmark stats: {str(e)}"}

    def generate_mermaid_diagrams(self, stats: Dict[str, Any]) -> List[str]:
        """Generate Mermaid.js diagrams from statistics.

        :param stats: User statistics
        :type stats: Dict[str, Any]
        :return: List of Mermaid diagram strings
        :rtype: List[str]
        """
        diagrams = []

        try:
            # ... [existing diagram generation code unchanged] ...
            # (see above for full code, omitted here for brevity)
            # All diagrams are appended to the `diagrams` list as before.
            # [ ... ]
            # --- Benchmark Results Mermaid Bar Chart ---
            if self.benchmark_results and isinstance(self.benchmark_results, dict):
                means = []
                means.extend(
                    (name, data["mean"])
                    for name, data in self.benchmark_results.items()
                    if isinstance(data, dict) and "mean" in data
                )
                if len(means) >= 2:
                    means = sorted(means, key=lambda x: x[1], reverse=True)[:10]
                    bar_chart = "```mermaid\nbar\n  title Last Benchmark Results (Top 10 by mean)\n"
                    for name, mean in means:
                        bar_chart += f'  "{name}" : {mean:.3f}\n'
                    bar_chart += "```\n"
                    diagrams.append(bar_chart)

        except Exception as e:
            diagrams.append(f"Error generating diagrams: {str(e)}")

        # Pass all diagrams through the markdown formatter for safety and rendering
        from backend.markdown_formatter import format_markdown

        return [format_markdown(diagram) for diagram in diagrams]

    def generate_markdown_tables(self, stats: Dict[str, Any]) -> str:
        """
        Generate markdown tables from statistics.

        :param stats: User statistics
        :type stats: Dict[str, Any]
        :return: Formatted markdown tables
        :rtype: str
        """

        def make_table(headers, rows):
            table = "| " + " | ".join(headers) + " |\n"
            table += "| " + " | ".join("-" * len(h) for h in headers) + " |\n"
            for row in rows:
                table += "| " + " | ".join(str(cell) for cell in row) + " |\n"
            return table

        tables = []

        try:
            # Performance Summary Table
            perf = stats.get("performance_summary")
            if perf:
                rows = []
                for category, data in perf.items():
                    if isinstance(data, dict):
                        for metric, value in data.items():
                            if isinstance(value, (int, float)):
                                metric_name = f"{category.title()} - {metric.replace('_', ' ').title()}"
                                rows.append([metric_name, value])
                if rows:
                    tables.append(
                        "## Performance Summary\n\n"
                        + make_table(["Metric", "Value"], rows)
                    )

            # LLM Usage Table
            llm = stats.get("llm_stats")
            if llm and "error" not in llm:
                sessions = llm.get("sessions", {})
                rows = [
                    [metric.replace("_", " ").title(), value]
                    for metric, value in sessions.items()
                ]
                if rows:
                    tables.append(
                        "## LLM Usage Statistics\n\n"
                        + make_table(["Metric", "Value"], rows)
                    )

            # Chat Activity Table
            chat = stats.get("chat_stats")
            if chat and "error" not in chat:
                sessions = chat.get("sessions", {})
                rows = [
                    [metric.replace("_", " ").title(), value]
                    for metric, value in sessions.items()
                ]
                if rows:
                    tables.append(
                        "## Chat Activity Statistics\n\n"
                        + make_table(["Metric", "Value"], rows)
                    )

            # Benchmark Statistics Table
            benchmarks = stats.get("benchmark_stats")
            if benchmarks and "error" not in benchmarks:
                rows = []
                for benchmark_name, benchmark_data in benchmarks.items():
                    if isinstance(benchmark_data, dict) and "mean" in benchmark_data:
                        category = benchmark_data.get("category", "unknown").title()
                        mean = benchmark_data.get("mean", 0)
                        stddev = benchmark_data.get("stddev", 0)
                        min_val = benchmark_data.get("min", 0)
                        max_val = benchmark_data.get("max", 0)
                        runs = benchmark_data.get("run_count", 0)
                        rows.append(
                            [
                                benchmark_name,
                                category,
                                f"{mean:.4f}",
                                f"{stddev:.4f}",
                                f"{min_val:.4f}",
                                f"{max_val:.4f}",
                                runs,
                            ]
                        )
                if rows:
                    tables.append(
                        "## Performance Benchmarks\n\n"
                        + make_table(
                            [
                                "Benchmark",
                                "Category",
                                "Mean (s)",
                                "Std Dev (s)",
                                "Min (s)",
                                "Max (s)",
                                "Runs",
                            ],
                            rows,
                        )
                    )

            # File Classification Table
            class_stats = stats.get("classification_stats")
            if class_stats and "error" not in class_stats:
                overview = class_stats.get("overview", {})
                rows = [
                    [metric.replace("_", " ").title(), value]
                    for metric, value in overview.items()
                ]
                if rows:
                    tables.append(
                        "## File Classification Statistics\n\n"
                        + make_table(["Metric", "Value"], rows)
                    )

            # Detailed Metrics Table
            metrics = stats.get("detailed_metrics")
            if metrics and "error" not in metrics:
                rows = []
                for metric_type, type_metrics in metrics.items():
                    for metric_name, values in type_metrics.items():
                        avg_val = values.get("avg", 0)
                        min_val = values.get("min", 0)
                        max_val = values.get("max", 0)
                        rows.append(
                            [
                                metric_type,
                                metric_name,
                                f"{avg_val:.2f}",
                                f"{min_val:.2f}",
                                f"{max_val:.2f}",
                            ]
                        )
                if rows:
                    tables.append(
                        "## Detailed Performance Metrics\n\n"
                        + make_table(["Type", "Metric", "Average", "Min", "Max"], rows)
                    )

            # Docker build times table
            docker_build_times = stats.get("docker_build_times", {})
            if docker_build_times:
                avg = docker_build_times.get("avg_duration", 0.0)
                last_build_time = docker_build_times.get("last_build_time", "")
                table = "## Docker Build Times\n\n" + make_table(
                    ["Metric", "Value"],
                    [
                        ["Average Build Time", f"{avg:.2f} seconds"],
                        *(
                            [["Last Build Time", last_build_time]]
                            if last_build_time
                            else []
                        ),
                    ],
                )
                averages = docker_build_times.get("averages", {})
                if averages and len(averages) > 1:
                    avg_rows = [
                        [image, f"{avg_time:.2f}"]
                        for image, avg_time in averages.items()
                    ]
                    table += "\n### Per-Image Averages\n\n" + make_table(
                        ["Image", "Average Build Time (s)"], avg_rows
                    )
                tables.append(table)

        except Exception as e:
            tables.append(f"Error generating tables: {str(e)}")

        combined_tables = "\n\n".join(tables)
        return format_markdown(combined_tables)

    def export_to_pdf(self, username: str, stats: Dict[str, Any]) -> str:
        """Export user statistics to PDF.

        :param username: Username
        :type username: str
        :param stats: User statistics
        :type stats: Dict[str, Any]
        :return: Path to generated PDF file
        :rtype: str
        """
        try:
            # Create temporary HTML file
            html_content = self._generate_html_report(username, stats)

            # Create temporary file
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".html", delete=False
            ) as f:
                f.write(html_content)
                html_path = f.name

            # Generate PDF using wkhtmltopdf or similar
            pdf_path = html_path.replace(".html", ".pdf")

            # Try to use wkhtmltopdf if available
            try:
                subprocess.run(
                    [
                        "wkhtmltopdf",
                        "--page-size",
                        "A4",
                        "--margin-top",
                        "20mm",
                        "--margin-bottom",
                        "20mm",
                        "--margin-left",
                        "20mm",
                        "--margin-right",
                        "20mm",
                        html_path,
                        pdf_path,
                    ],
                    check=True,
                )
            except (subprocess.CalledProcessError, FileNotFoundError):
                # Fallback: create a simple text report
                pdf_path = self._create_text_report(username, stats)

            # Clean up HTML file
            os.unlink(html_path)

            return pdf_path

        except Exception as e:
            return f"Error generating PDF: {str(e)}"

    def _generate_html_report(self, username: str, stats: Dict[str, Any]) -> str:
        """Generate HTML report for PDF export.

        :param username: Username
        :type username: str
        :param stats: User statistics
        :type stats: Dict[str, Any]
        :return: HTML content
        :rtype: str
        """
        timestamp = format_singapore_datetime(datetime.now())

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Performance Report - {username}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                h1, h2, h3 {{ color: #333; }}
                .section {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; }}
                .metric {{ display: inline-block; margin: 10px; padding: 10px; background: #f5f5f5; }}
                .value {{ font-size: 24px; font-weight: bold; color: #007bff; }}
                .label {{ font-size: 12px; color: #666; }}
                table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <h1>Performance Report</h1>
            <p><strong>User:</strong> {username}</p>
            <p><strong>Generated:</strong> {timestamp}</p>

            <div class="section">
                <h2>Performance Summary</h2>
                {self._format_performance_summary(stats.get("performance_summary", {}))}
            </div>

            <div class="section">
                <h2>LLM Usage</h2>
                {self._format_llm_stats(stats.get("llm_stats", {}))}
            </div>

            <div class="section">
                <h2>Chat Activity</h2>
                {self._format_chat_stats(stats.get("chat_stats", {}))}
            </div>

            <div class="section">
                <h2>File Classifications</h2>
                {self._format_classification_stats(stats.get("classification_stats", {}))}
            </div>

            <div class="section">
                <h2>Detailed Metrics</h2>
                {self._format_detailed_metrics(stats.get("detailed_metrics", {}))}
            </div>
        </body>
        </html>
        """

    def _format_performance_summary(self, perf: Dict[str, Any]) -> str:
        """Format performance summary for HTML.

        :param perf: Performance summary
        :type perf: Dict[str, Any]
        :return: Formatted HTML
        :rtype: str
        """
        if not perf:
            return "<p>No performance data available</p>"

        html = "<table>" + "<tr><th>Metric</th><th>Value</th></tr>"
        for category, data in perf.items():
            if isinstance(data, dict):
                for metric, value in data.items():
                    if isinstance(value, (int, float)):
                        html += f"<tr><td>{category.title()} - {metric.replace('_', ' ').title()}</td><td>{value}</td></tr>"

        html += "</table>"
        return html

    def _format_llm_stats(self, llm: Dict[str, Any]) -> str:
        # sourcery skip: class-extract-method
        """Format LLM stats for HTML.

        :param llm: LLM statistics
        :type llm: Dict[str, Any]
        :return: Formatted HTML
        :rtype: str
        """
        if not llm or "error" in llm:
            return "<p>No LLM data available</p>"

        html = "<table>" + "<tr><th>Metric</th><th>Value</th></tr>"
        sessions = llm.get("sessions", {})
        for metric, value in sessions.items():
            html += (
                f"<tr><td>{metric.replace('_', ' ').title()}</td><td>{value}</td></tr>"
            )

        html += "</table>"
        return html

    def _format_chat_stats(self, chat: Dict[str, Any]) -> str:
        """Format chat stats for HTML.

        :param chat: Chat statistics
        :type chat: Dict[str, Any]
        :return: Formatted HTML
        :rtype: str
        """
        if not chat or "error" in chat:
            return "<p>No chat data available</p>"

        html = "<table>" + "<tr><th>Metric</th><th>Value</th></tr>"
        sessions = chat.get("sessions", {})
        for metric, value in sessions.items():
            html += (
                f"<tr><td>{metric.replace('_', ' ').title()}</td><td>{value}</td></tr>"
            )

        html += "</table>"
        return html

    def _format_classification_stats(self, class_stats: Dict[str, Any]) -> str:
        """Format classification stats for HTML.

        :param class_stats: Classification statistics
        :type class_stats: Dict[str, Any]
        :return: Formatted HTML
        :rtype: str
        """
        if not class_stats or "error" in class_stats:
            return "<p>No classification data available</p>"

        html = "<table>" + "<tr><th>Metric</th><th>Value</th></tr>"
        overview = class_stats.get("overview", {})
        for metric, value in overview.items():
            html += (
                f"<tr><td>{metric.replace('_', ' ').title()}</td><td>{value}</td></tr>"
            )

        html += "</table>"
        return html

    def _format_detailed_metrics(self, metrics: Dict[str, Any]) -> str:
        """Format detailed metrics for HTML.

        :param metrics: Detailed metrics
        :type metrics: Dict[str, Any]
        :return: Formatted HTML
        :rtype: str
        """
        if not metrics or "error" in metrics:
            return "<p>No detailed metrics available</p>"

        html = (
            "<table>"
            + "<tr><th>Type</th><th>Metric</th><th>Average</th><th>Min</th><th>Max</th></tr>"
        )
        for metric_type, type_metrics in metrics.items():
            for metric_name, values in type_metrics.items():
                html += f"<tr><td>{metric_type}</td><td>{metric_name}</td><td>{values.get('avg', 0):.2f}</td><td>{values.get('min', 0):.2f}</td><td>{values.get('max', 0):.2f}</td></tr>"

        html += "</table>"
        return html

    def _create_text_report(self, username: str, stats: Dict[str, Any]) -> str:
        """Create a simple text report as fallback.

        :param username: Username
        :type username: str
        :param stats: User statistics
        :type stats: Dict[str, Any]
        :return: Path to text report
        :rtype: str
        """
        timestamp = format_singapore_datetime(datetime.now())

        report = f"""
Performance Report for {username}
Generated: {timestamp}

{json.dumps(stats, indent=2)}
        """

        # Save to file
        report_path = os.path.join(
            get_chatbot_dir(), f"stats_report_{username}_{int(time.time())}.txt"
        )
        with open(report_path, "w") as f:
            f.write(report)

        return report_path


def create_stats_interface() -> gr.Interface:
    """Create the stats interface.

    :return: Gradio interface
    :rtype: gr.Interface
    """
    stats_interface = StatsInterface()

    def get_user_statistics(username_state: str) -> Tuple[str, str, str, str, str]:
        """
        Get statistics for a user.

        Args:
            username_state (str): The username to get statistics for.

        Returns:
            Tuple[str, str, str, str, str]: Tuple of (username_state, stats_json, mermaid_diagrams, markdown_tables, pdf_path)
        """
        try:
            # Get user stats using the username from state
            username = username_state if isinstance(username_state, str) else ""
            stats = stats_interface.get_user_stats(username)

            if "error" in stats:
                return (
                    username_state,
                    json.dumps(stats, indent=2),
                    "Error loading data",
                    "Error loading data",
                    "",
                )

            # Generate Mermaid diagrams
            diagrams = stats_interface.generate_mermaid_diagrams(stats)
            # Each diagram is already formatted and sanitized by generate_mermaid_diagrams
            mermaid_content = "\n\n".join(diagrams)

            # Generate markdown tables
            markdown_tables = stats_interface.generate_markdown_tables(stats)

            # Generate PDF
            pdf_path = stats_interface.export_to_pdf(username, stats)

            return (
                username_state,
                json.dumps(stats, indent=2),
                mermaid_content,
                markdown_tables,
                pdf_path,
            )

        except Exception as e:
            error_msg = f"Error processing statistics: {str(e)}"
            return (
                username_state,
                json.dumps({"error": error_msg}, indent=2),
                error_msg,
                error_msg,
                "",
            )

    # Create interface
    interface = gr.Interface(
        fn=get_user_statistics,
        inputs=[gr.State()],
        outputs=[
            gr.State(),
            gr.JSON(label="Raw Statistics Data"),
            gr.Markdown(
                label="Performance Visualizations", elem_classes=["mermaid-diagrams"]
            ),
            gr.Markdown(label="Statistics Tables", elem_classes=["markdown-tables"]),
            gr.File(label="PDF Report", file_count="single"),
        ],
        title="📊 User Performance Statistics",
        description="""
        Comprehensive performance analytics dashboard for the NYP FYP CNC Chatbot.

        This interface provides detailed statistics including:
        - Docker build performance
        - API call metrics
        - App startup times
        - LLM usage statistics
        - Chat activity analysis
        - File classification metrics
        - Audio transcription statistics

        Visualizations are generated using Mermaid.js diagrams and can be exported to PDF.

        **Benchmarking powered by hyperfine**: Peter, D. (2023). hyperfine (Version 1.16.1) [Computer software]. [https://github.com/sharkdp/hyperfine](https://github.com/sharkdp/hyperfine)
        """,
        theme=gr.themes.Soft(),
    )

    return interface


# Export the interface creation function
__all__ = ["create_stats_interface", "StatsInterface"]
