"""
Classification Formatter Module for NYP FYP Chatbot

This module provides formatting utilities for classification results, including security classification, sensitivity, and recommendations, for display in the Gradio UI.
"""

import json
from typing import Dict, Any, List  # noqa: F401
from datetime import datetime  # noqa: F401
import ast  # Required for literal_eval, use with caution for untrusted inputs


def format_classification_response(
    classification_data_raw: Any,
    extraction_result: Dict[str, Any],
    original_filename: str,
) -> Dict[str, str]:
    """
    Formats the security classification and content extraction results for display
    within a Gradio interface.
    """

    def parse_dict_or_json(data):
        if isinstance(data, dict):
            return data
        if isinstance(data, str):
            try:
                return json.loads(data)
            except Exception:
                try:
                    return ast.literal_eval(data)
                except Exception:
                    return {}
        return {}

    classification_data = parse_dict_or_json(classification_data_raw)
    classification_details = classification_data.get("classification", {})
    if not isinstance(classification_details, dict):
        classification_details = {}

    original_text_sample = str(classification_details.get("input", ""))
    if len(original_text_sample) > 500:
        original_text_sample = f"{original_text_sample[:500]}..."

    llm_output = classification_details.get(
        "answer", classification_details
    ) or classification_data.get("ANSWER", {})
    llm_output = parse_dict_or_json(llm_output)

    classification_category = str(llm_output.get("classification", "Unknown"))
    sensitivity_level = str(llm_output.get("sensitivity", "Unknown"))
    reasoning = str(llm_output.get("reasoning", "No reasoning provided."))

    file_size_bytes = extraction_result.get("file_size", 0)
    file_size_kb = file_size_bytes / 1024
    extraction_method = extraction_result.get("method", "Unknown")
    extraction_error = extraction_result.get("error", "")
    extraction_error_display = (
        f"<p style='color:red;'>Extraction Error: {extraction_error}</p>"
        if extraction_error
        else ""
    )
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    handling_recommendations = get_handling_recommendations(
        security_class=classification_category,
        sensitivity=sensitivity_level,
    )
    if handling_recommendations:
        recommendations_html = (
            "<h4>Handling Recommendations:</h4><ul>"
            + "".join(f"<li>{rec}</li>" for rec in handling_recommendations)
            + "</ul>"
        )
    else:
        recommendations_html = "<p>No specific handling recommendations available for this classification.</p>"

    def highlight_color(val, red_terms, green="#28a745"):
        return "red" if any(term in val.lower() for term in red_terms) else green

    results_box_content = (
        f"<div style=\"font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; padding: 15px; border-radius: 8px; background-color: #f9f9f9; border: 1px solid #e0e0e0; box-shadow: 0 2px 5px rgba(0,0,0,0.05);\">"
        f'<h3 style="color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px; margin-bottom: 15px;">Classification Results</h3>'
        f'<p><strong>File:</strong> <span style="color: #0056b3;">{original_filename}</span> (Size: {file_size_kb:.2f} KB, Extracted by: {extraction_method})</p>'
        f"{extraction_error_display}"
        f"<p><strong>Timestamp:</strong> {current_time}</p>"
        f'<p><strong>Security Classification:</strong> <span style="font-weight: bold; color: {highlight_color(classification_category, ["restricted", "secret"])};">{classification_category}</span></p>'
        f'<p><strong>Sensitivity Level:</strong> <span style="font-weight: bold; color: {highlight_color(sensitivity_level, ["high"])};">{sensitivity_level}</span></p>'
        f"<p><strong>Keywords (LLM):</strong> N/A</p>"
        f"{recommendations_html}"
        f"</div>"
    )

    classification_result_md = (
        f"### Security Classification\n\n"
        f"<span style='font-size: 1.2em; font-weight: bold; color: {highlight_color(classification_category, ['restricted', 'secret'])};'>{classification_category}</span>"
    )
    sensitivity_result_md = (
        f"### Sensitivity Level\n\n"
        f"<span style='font-size: 1.2em; font-weight: bold; color: {highlight_color(sensitivity_level, ['high'])};'>{sensitivity_level}</span>"
    )
    file_info_md = (
        f"### File Information\n\n"
        f"- **Original Filename:** {original_filename}\n"
        f"- **Size:** {file_size_kb:.2f} KB\n"
        f"- **Extraction Method:** {extraction_method}\n"
        f"- **Extracted Content Sample:**\n```\n{original_text_sample}\n```\n"
        f"{extraction_error_display}"
    )
    reasoning_md = f"### Reasoning\n\n{reasoning}"
    summary_md = (
        f"### Classification Summary\n\n"
        f"Based on the content analysis, the document '{original_filename}' has been classified as **{classification_category}** with **{sensitivity_level}** sensitivity.\n\n"
        f"**Keywords:** N/A\n\n"
        f"{recommendations_html}"
    )
    return {
        "results_box": results_box_content,
        "classification": classification_result_md,
        "sensitivity": sensitivity_result_md,
        "file_info": file_info_md,
        "reasoning": reasoning_md,
        "summary": summary_md,
    }


def get_handling_recommendations(security_class: str, sensitivity: str) -> List[str]:
    """
    Generates handling recommendations based on security classification and sensitivity.
    """

    recommendations = []

    security = security_class.lower()
    sensitivity = sensitivity.lower()

    if "restricted" in security or "secret" in security:
        recommendations.extend(
            [
                "Store in secure, access-controlled location",
                "Limit access to authorized personnel only",
                "Use encrypted transmission methods",
                "Follow organizational security protocols",
            ]
        )
    elif "confidential" in security:
        recommendations.extend(
            [
                "Restrict access to need-to-know basis",
                "Use secure communication channels",
                "Store in protected systems",
            ]
        )
    elif "official" in security and "closed" in security:
        recommendations.extend(
            [
                "Limit distribution within organization",
                "Follow internal sharing guidelines",
            ]
        )
    elif "public" in security or ("official" in security and "open" in security):
        recommendations.extend(
            [
                "May be shared publicly as appropriate",
                "Follow standard information sharing practices",
            ]
        )

    if "high" in sensitivity:
        recommendations.append("Exercise extra caution in handling and sharing")
    elif "medium" in sensitivity:
        recommendations.append("Apply standard sensitivity controls")

    return recommendations
