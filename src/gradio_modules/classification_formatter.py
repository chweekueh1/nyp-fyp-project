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

    This function ensures all output strings are correctly cast to prevent potential
    'AddableValuesDict' errors, provides clear summaries, and includes basic styling
    for visibility. It also handles the case where the raw classification data
    might be a string representation of a dictionary (e.g., JSON string), AND
    where the nested 'answer' field might be a JSON string that needs parsing.

    :param classification_data_raw: The raw classification results, which might be a
                                   dictionary or a string representation of a dictionary.
                                   The function will now also parse the 'answer' field
                                   if it is a JSON string.
    :type classification_data_raw: Any
    :param extraction_result: A dictionary containing details from the content
                               extraction process, expected to include 'content' (a
                               sample of the extracted text), 'file_size', and 'method'.
    :type extraction_result: Dict[str, Any]
    :param original_filename: The original name of the file that was processed.
    :type original_filename: str
    :return: A dictionary containing formatted string outputs suitable for
             Gradio components.
    :rtype: Dict[str, str]
    """
    # --- DEBUG PRINT AT THE START ---
    print(
        f"DEBUG: Entering format_classification_response with classification_data_raw: {classification_data_raw}"
    )
    print(
        f"DEBUG: type(classification_data_raw) received: {type(classification_data_raw)}"
    )
    # --- END DEBUG PRINT ---

    classification_data: Dict[
        str, Any
    ] = {}  # This will store the *parsed* outermost dictionary

    if isinstance(classification_data_raw, str):
        try:
            # Attempt to parse as JSON first (as per system_prompts.py expectations)
            classification_data = json.loads(classification_data_raw)
            print("DEBUG: Successfully parsed classification_data_raw as JSON.")
        except json.JSONDecodeError as e:
            print(
                f"ERROR: classification_data_raw is a string but not valid JSON. Attempting ast.literal_eval (risky). Error: {e}"
            )
            try:
                # Fallback for Python dictionary string representation (e.g., output of str(some_dict))
                # This should ideally be fixed upstream to output proper JSON.
                classification_data = ast.literal_eval(classification_data_raw)
                print(
                    "DEBUG: Successfully parsed classification_data_raw using ast.literal_eval. Please ensure upstream provides valid JSON."
                )
            except (ValueError, SyntaxError) as e_ast:
                print(
                    f"CRITICAL ERROR: Could not parse classification_data_raw string. Ensure upstream provides valid JSON or a Python dictionary directly. Error: {e_ast}. Original string fragment: {str(classification_data_raw)[:200]}..."
                )
                classification_data = {}  # Fallback to empty dictionary if all parsing fails
    elif isinstance(classification_data_raw, dict):
        # If it's already a dictionary, use it directly
        classification_data = classification_data_raw
    else:
        print(
            f"CRITICAL ERROR: Unexpected type for classification_data_raw: {type(classification_data_raw)}. Expected str or dict."
        )
        classification_data = {}  # Fallback to empty dictionary

    # Now 'classification_data' is guaranteed to be a dictionary (or empty if parsing failed).
    # Proceed with the rest of the logic using this processed dictionary.

    # Extract original text if available from 'input' field in the raw classification data
    original_text_sample = ""
    # Safely get the 'classification' dictionary first from classification_data
    classification_details_from_raw = classification_data.get("classification")

    if isinstance(classification_details_from_raw, dict):
        original_text_sample = str(classification_details_from_raw.get("input", ""))
        # Truncate for display if it's too long
        if len(original_text_sample) > 500:
            original_text_sample = original_text_sample[:500] + "..."

    # Determine the actual source of classification details
    potential_llm_output: Any = None

    if isinstance(classification_details_from_raw, dict):
        # Prioritize classification_data['classification']['answer']
        if "answer" in classification_details_from_raw:
            potential_llm_output = classification_details_from_raw["answer"]
        else:
            # Fallback to classification_data['classification'] if no 'answer' key
            # This handles cases where the LLM output is directly under 'classification'
            potential_llm_output = classification_details_from_raw

    # If no classification details found yet, try top-level 'ANSWER'
    if potential_llm_output is None:
        potential_llm_output = classification_data.get("ANSWER")

    # --- FIX START: Ensure the parsed LLM output (from 'answer' or 'ANSWER') is a dictionary ---
    parsed_llm_output: Dict[str, Any] = {}
    if isinstance(potential_llm_output, dict):
        parsed_llm_output = potential_llm_output
    elif isinstance(potential_llm_output, str):
        print(
            f"DEBUG: Inner classification output is a string. Attempting to parse it. Value: {potential_llm_output}"
        )
        try:
            parsed_llm_output = json.loads(potential_llm_output)
            print(
                "DEBUG: Successfully parsed inner classification output string as JSON."
            )
        except json.JSONDecodeError as e:
            print(
                f"ERROR: Could not parse inner classification output string as JSON. Error: {e}. Value: {potential_llm_output[:100]}..."
            )
            parsed_llm_output = {}  # Fallback to empty dict on parsing failure
    else:
        print(
            f"Warning: Classification output (from 'answer' or 'ANSWER' field) is neither a dictionary nor a parseable string. Received type: {type(potential_llm_output)}. Value: {potential_llm_output}"
        )
        parsed_llm_output = {}  # Default to empty dict
    # --- FIX END ---

    # Safely extract values using .get() with default fallbacks
    # Ensure all extracted values are cast to string for Gradio compatibility
    classification_category = str(parsed_llm_output.get("classification", "Unknown"))
    sensitivity_level = str(parsed_llm_output.get("sensitivity", "Unknown"))
    reasoning = str(parsed_llm_output.get("reasoning", "No reasoning provided."))

    # Get file details from extraction_result
    file_size_bytes = extraction_result.get("file_size", 0)
    file_size_kb = file_size_bytes / 1024
    extraction_method = extraction_result.get("method", "Unknown")

    # Get any extraction error message
    extraction_error = extraction_result.get("error", "")
    extraction_error_display = (
        f"<p style='color:red;'>Extraction Error: {extraction_error}</p>"
        if extraction_error
        else ""
    )

    # Format current timestamp
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # --- Section for Recommendations ---
    # Call the helper function to get handling recommendations
    handling_recommendations = get_handling_recommendations(
        security_class=classification_category,
        sensitivity=sensitivity_level,
    )
    recommendations_html = ""
    if handling_recommendations:
        recommendations_html = (
            "<h4>Handling Recommendations:</h4><ul>"
            + "".join([f"<li>{rec}</li>" for rec in handling_recommendations])
            + "</ul>"
        )
    else:
        recommendations_html = "<p>No specific handling recommendations available for this classification.</p>"
    # --- End Recommendations Section ---

    # Format outputs for Gradio components
    results_box_content = f"""
    <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; padding: 15px; border-radius: 8px; background-color: #f9f9f9; border: 1px solid #e0e0e0; box-shadow: 0 2px 5px rgba(0,0,0,0.05);">
        <h3 style="color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px; margin-bottom: 15px;">Classification Results</h3>
        <p><strong>File:</strong> <span style="color: #0056b3;">{original_filename}</span> (Size: {file_size_kb:.2f} KB, Extracted by: {extraction_method})</p>
        {extraction_error_display}
        <p><strong>Timestamp:</strong> {current_time}</p>
        <p><strong>Security Classification:</strong> <span style="font-weight: bold; color: {"red" if "restricted" in classification_category.lower() or "secret" in classification_category.lower() else "#28a745"};">{classification_category}</span></p>
        <p><strong>Sensitivity Level:</strong> <span style="font-weight: bold; color: {"red" if "high" in sensitivity_level.lower() else "#28a745"};">{sensitivity_level}</span></p>
        <p><strong>Keywords (LLM):</strong> N/A</p>
        {recommendations_html}
    </div>
    """

    classification_result_md = f"### Security Classification\n\n<span style='font-size: 1.2em; font-weight: bold; color: {'red' if 'restricted' in classification_category.lower() or 'secret' in classification_category.lower() else '#28a745'};'>{classification_category}</span>"
    sensitivity_result_md = f"### Sensitivity Level\n\n<span style='font-size: 1.2em; font-weight: bold; color: {'red' if 'high' in sensitivity_level.lower() else '#28a745'};'>{sensitivity_level}</span>"
    file_info_md = f"### File Information\n\n- **Original Filename:** {original_filename}\n- **Size:** {file_size_kb:.2f} KB\n- **Extraction Method:** {extraction_method}\n- **Extracted Content Sample:**\n```\n{original_text_sample}\n```\n{extraction_error_display}"
    reasoning_md = f"### Reasoning\n\n{reasoning}"
    summary_md = f"""
    ### Classification Summary

    Based on the content analysis, the document '{original_filename}' has been classified as **{classification_category}** with **{sensitivity_level}** sensitivity.

    **Keywords:** N/A

    {recommendations_html}
    """
    returned_dict = {
        "results_box": results_box_content,
        "classification": classification_result_md,
        "sensitivity": sensitivity_result_md,
        "file_info": file_info_md,
        "reasoning": reasoning_md,
        "summary": summary_md,
    }

    return returned_dict


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
