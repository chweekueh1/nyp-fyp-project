import json
from typing import Dict, Any, List, Optional
from datetime import datetime


def format_classification_response(
    classification_data: Dict[str, Any],
    extraction_result: Dict[str, Any],
    original_filename: str,
) -> Dict[str, str]:
    """
    Formats the security classification and content extraction results for display
    within a Gradio interface. This function ensures all output strings are
    correctly cast to prevent potential 'AddableValuesDict' errors, provides
    clear summaries, and includes basic styling for visibility.

    :param classification_data: A dictionary containing the classification results
                                 from the model. It might contain a top-level 'ANSWER'
                                 key whose value is a JSON string of the actual
                                 classification details, or it might directly contain
                                 'classification', 'sensitivity', 'reasoning', etc.
    :type classification_data: Dict[str, Any]
    :param extraction_result: A dictionary containing details from the content
                               extraction process, expected to include 'content' (a
                               sample of the extracted text), 'file_size', and 'method'.
    :type extraction_result: Dict[str, Any]
    :param original_filename: The original name of the file that was processed.
    :type original_filename: str
    :return: A dictionary containing formatted string outputs suitable for direct
             display in Gradio components, including 'classification', 'sensitivity',
             'file_info', 'reasoning', and 'summary'.
    :rtype: Dict[str, str]
    """

    # Determine the actual source of classification details
    # Prioritize parsing 'ANSWER' if it's a JSON string
    actual_classification_details = {}
    if "ANSWER" in classification_data and isinstance(
        classification_data["ANSWER"], str
    ):
        try:
            actual_classification_details = json.loads(classification_data["ANSWER"])
        except json.JSONDecodeError:
            # If parsing fails, fall back to using classification_data directly,
            # assuming it might contain the keys at the top level or for error reporting
            actual_classification_details = classification_data
    else:
        # If 'ANSWER' key is not present or not a string, assume classification_data
        # itself contains the classification details directly.
        actual_classification_details = classification_data

    # --- Robustly convert classification and sensitivity to strings and then to uppercase ---
    # Retrieve with a default, then convert to string, then apply .upper()
    # Check both potential key names (e.g., "CLASSIFICATION" vs "classification")
    classification_category = str(
        actual_classification_details.get(
            "CLASSIFICATION",
            actual_classification_details.get("classification", "Unknown"),
        )
    ).upper()
    sensitivity_level = str(
        actual_classification_details.get(
            "SENSITIVITY",
            actual_classification_details.get("sensitivity", "Non-Sensitive"),
        )
    ).upper()
    reasoning = str(
        actual_classification_details.get(
            "REASONING",
            actual_classification_details.get(
                "reasoning", "No specific reasoning provided."
            ),
        )
    )

    # Confidence can be a number, retrieve and handle accordingly for display
    # Check both potential key names (e.g., "CONFIDENCE" vs "confidence")
    confidence = actual_classification_details.get(
        "CONFIDENCE", actual_classification_details.get("confidence", None)
    )
    confidence_str = (
        f"{confidence * 100:.2f}%" if isinstance(confidence, (int, float)) else "N/A"
    )

    # --- Robustly convert extracted_content_sample to string ---
    extracted_content_sample = str(extraction_result.get("content", "")).strip()
    if len(extracted_content_sample) > 500:
        extracted_content_sample = extracted_content_sample[:500] + "..."

    # --- Construct file information string, ensuring all parts are strings ---
    file_info_str = (
        f"**Original Filename:** {str(original_filename)}\n"
        f"**File Size:** {str(extraction_result.get('file_size', 'N/A'))} bytes\n"
        f"**Extraction Method:** {str(extraction_result.get('method', 'N/A'))}\n"
        f"**Extracted Content Sample (first 500 chars):**\n```\n{extracted_content_sample}\n```"
    )

    # --- Construct summary text, ensuring all parts are strings ---
    summary_text = (
        f"## Classification Summary\n\n"
        f"**File:** `{str(original_filename)}`\n"
        f"**Security Classification:** **<span style='color: {'red' if 'RESTRICTED' in classification_category or 'CONFIDENTIAL' in classification_category else 'green'};'>{classification_category}</span>**\n"
        f"**Sensitivity Level:** **<span style='color: {'orange' if 'SENSITIVE' in sensitivity_level else 'blue'};'>{sensitivity_level}</span>**\n\n"
        f"**Reasoning:**\n{reasoning}\n\n"
        f"**Confidence:** {confidence_str}\n"
    )

    return {
        "classification": classification_category,
        "sensitivity": sensitivity_level,
        "file_info": file_info_str,
        "reasoning": reasoning,
        "summary": summary_text,
    }


def format_security_classification(classification: str) -> str:
    """Format security classification with appropriate styling.

    :param classification: The security classification string
    :type classification: str
    :return: Formatted classification with emoji and styling
    :rtype: str
    """

    # Classification mapping with emojis and colors
    class_mapping = {
        "RESTRICTED": "🔴 **RESTRICTED**",
        "CONFIDENTIAL": "🟠 **CONFIDENTIAL**",
        "SECRET": "🔴 **SECRET**",
        "TOP SECRET": "⚫ **TOP SECRET**",
        "OFFICIAL(OPEN)": "🟢 **OFFICIAL (OPEN)**",
        "OFFICIAL(CLOSED)": "🟡 **OFFICIAL (CLOSED)**",
        "OFFICIAL": "🟢 **OFFICIAL**",
        "PUBLIC": "🟢 **PUBLIC**",
        "UNCLASSIFIED": "🟢 **UNCLASSIFIED**",
        "UNKNOWN": "⚪ **UNKNOWN**",
        "ERROR": "❌ **ERROR**",
    }

    # Normalize classification
    normalized = classification.upper().strip()

    # Handle variations
    if "OFFICIAL" in normalized and "OPEN" in normalized:
        normalized = "OFFICIAL(OPEN)"
    elif "OFFICIAL" in normalized and "CLOSED" in normalized:
        normalized = "OFFICIAL(CLOSED)"
    elif "TOP SECRET" in normalized:
        normalized = "TOP SECRET"

    formatted = class_mapping.get(normalized, f"⚪ **{classification.upper()}**")

    return formatted


def format_sensitivity_level(sensitivity: str) -> str:
    """Format sensitivity level with appropriate styling.

    :param sensitivity: The sensitivity level string
    :type sensitivity: str
    :return: Formatted sensitivity with emoji and styling
    :rtype: str
    """

    # Sensitivity mapping with emojis
    sensitivity_mapping = {
        "HIGH": "🔥 **HIGH SENSITIVITY**",
        "MEDIUM": "🟡 **MEDIUM SENSITIVITY**",
        "LOW": "🟢 **LOW SENSITIVITY**",
        "NON-SENSITIVE": "✅ **NON-SENSITIVE**",
        "SENSITIVE": "🟡 **SENSITIVE**",
        "UNKNOWN": "⚪ **UNKNOWN SENSITIVITY**",
        "ERROR": "❌ **ERROR**",
    }

    # Defensive: ensure sensitivity is a string
    if not isinstance(sensitivity, str):
        import logging

        logging.warning(
            f"format_sensitivity_level: expected string, got {type(sensitivity)}: {sensitivity}"
        )
        sensitivity = str(sensitivity) if sensitivity is not None else "UNKNOWN"

    normalized = sensitivity.upper().strip()
    formatted = sensitivity_mapping.get(normalized, f"⚪ **{normalized}**")

    return formatted


def format_file_information(
    file_info: Dict[str, str], extraction_info: Dict[str, Any]
) -> str:
    """Format file information with extraction details.

    :param file_info: Basic file information dictionary
    :type file_info: Dict[str, str]
    :param extraction_info: Information about content extraction
    :type extraction_info: Dict[str, Any]
    :return: Formatted file information string
    :rtype: str
    """

    lines = []

    # Basic file info
    if "filename" in file_info:
        lines.append(f"📄 **Filename:** {file_info['filename']}")

    if "size" in file_info:
        size_bytes = int(file_info["size"])
        size_formatted = format_file_size(size_bytes)
        lines.append(f"📏 **Size:** {size_formatted}")

    if "saved_name" in file_info:
        lines.append(f"💾 **Saved as:** {file_info['saved_name']}")

    # Extraction information
    if extraction_info:
        file_type = extraction_info.get("file_type", "unknown")
        lines.append(f"📋 **Type:** {file_type.upper()}")

        method = extraction_info.get("method", "unknown")
        method_formatted = format_extraction_method(method)
        lines.append(f"🔧 **Extraction:** {method_formatted}")

        # Content length
        content = extraction_info.get("content", "")
        if content:
            char_count = len(content)
            word_count = len(content.split())
            lines.append(
                f"📊 **Content:** {char_count:,} characters, {word_count:,} words"
            )

        # Methods tried
        methods_tried = extraction_info.get("extraction_methods_tried", [])
        if methods_tried:
            methods_str = ", ".join(methods_tried)
            lines.append(f"🔍 **Methods tried:** {methods_str}")

    # Timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines.append(f"⏰ **Processed:** {timestamp}")

    return "\n".join(lines)


def format_extraction_method(method: str) -> str:
    """Format extraction method with descriptive text.

    :param method: The extraction method name
    :type method: str
    :return: Formatted method description with emoji
    :rtype: str
    """

    method_descriptions = {
        "pandoc": "📚 Pandoc (Document Conversion)",
        "tesseract_ocr": "👁️ Tesseract OCR (Image Text Recognition)",
        "pdf_extraction": "📄 PDF Text Extraction",
        "text_file": "📝 Plain Text Reading",
        "fallback_original": "🔄 Legacy Extraction Method",
        "excel_fallback": "📊 Excel Processing",
        "none": "❌ No Extraction Performed",
        "error": "❌ Extraction Failed",
    }

    return method_descriptions.get(method, f"🔧 {method.replace('_', ' ').title()}")


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format.

    :param size_bytes: File size in bytes
    :type size_bytes: int
    :return: Human-readable file size string
    :rtype: str
    """

    if size_bytes < 1024:
        return f"{size_bytes} bytes"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


def format_reasoning(reasoning: str, confidence: Optional[float] = None) -> str:
    """Format classification reasoning with better structure.

    :param reasoning: The reasoning text from classification
    :type reasoning: str
    :param confidence: Confidence score (0.0 to 1.0)
    :type confidence: Optional[float]
    :return: Formatted reasoning with confidence and structure
    :rtype: str
    """

    lines = []

    # Add confidence if available
    if confidence is not None:
        confidence_pct = confidence * 100
        if confidence_pct >= 90:
            conf_emoji = "🎯"
            conf_desc = "Very High"
        elif confidence_pct >= 75:
            conf_emoji = "✅"
            conf_desc = "High"
        elif confidence_pct >= 60:
            conf_emoji = "🟡"
            conf_desc = "Medium"
        else:
            conf_emoji = "⚠️"
            conf_desc = "Low"

        lines.append(
            f"{conf_emoji} **Confidence:** {conf_desc} ({confidence_pct:.1f}%)"
        )
        lines.append("")

    # Format reasoning text
    if reasoning and reasoning.strip():
        lines.append("🧠 **Analysis:**")

        # Try to structure the reasoning if it's unformatted
        reasoning_lines = reasoning.strip().split("\n")
        for line in reasoning_lines:
            line = line.strip()
            if line:
                # Add bullet points if not already present
                if not line.startswith(("•", "-", "*", "1.", "2.", "3.")):
                    line = f"• {line}"
                lines.append(f"  {line}")
    else:
        lines.append("🤔 **Analysis:** No detailed reasoning provided")

    return "\n".join(lines)


def format_classification_summary(
    security_class: str,
    sensitivity: str,
    confidence: Optional[float] = None,
    extraction_info: Optional[Dict[str, Any]] = None,
) -> str:
    """Create a formatted summary of the classification.

    :param security_class: The security classification
    :type security_class: str
    :param sensitivity: The sensitivity level
    :type sensitivity: str
    :param confidence: Confidence score (0.0 to 1.0)
    :type confidence: Optional[float]
    :param extraction_info: Information about content extraction
    :type extraction_info: Optional[Dict[str, Any]]
    :return: Formatted summary markdown
    :rtype: str
    """

    lines = []
    lines.append("## 📋 Classification Summary")
    lines.append("")

    # Main classification
    security_formatted = format_security_classification(security_class)
    sensitivity_formatted = format_sensitivity_level(sensitivity)

    lines.append(f"**Security Level:** {security_formatted}")
    lines.append(f"**Sensitivity:** {sensitivity_formatted}")

    if confidence is not None:
        lines.append(f"**Confidence:** {confidence * 100:.1f}%")

    lines.append("")

    # Extraction status
    if extraction_info:
        method = extraction_info.get("method", "unknown")
        if method != "none" and method != "error":
            lines.append("✅ **Status:** Content successfully extracted and analyzed")
        else:
            lines.append("⚠️ **Status:** Limited analysis due to extraction issues")

        error = extraction_info.get("error")
        if error:
            lines.append(f"❌ **Issue:** {error}")

    lines.append("")

    # Recommendations based on classification
    recommendations = get_handling_recommendations(security_class, sensitivity)
    if recommendations:
        lines.append("💡 **Handling Recommendations:**")
        for rec in recommendations:
            lines.append(f"  • {rec}")

    return "\n".join(lines)


def get_handling_recommendations(security_class: str, sensitivity: str) -> List[str]:
    """Get handling recommendations based on classification.

    :param security_class: The security classification
    :type security_class: str
    :param sensitivity: The sensitivity level
    :type sensitivity: str
    :return: List of handling recommendations
    :rtype: List[str]
    """

    recommendations = []

    security_upper = security_class.upper()
    sensitivity_upper = sensitivity.upper()

    if "RESTRICTED" in security_upper or "SECRET" in security_upper:
        recommendations.extend(
            [
                "Store in secure, access-controlled location",
                "Limit access to authorized personnel only",
                "Use encrypted transmission methods",
                "Follow organizational security protocols",
            ]
        )
    elif "CONFIDENTIAL" in security_upper:
        recommendations.extend(
            [
                "Restrict access to need-to-know basis",
                "Use secure communication channels",
                "Store in protected systems",
            ]
        )
    elif "OFFICIAL" in security_upper and "CLOSED" in security_upper:
        recommendations.extend(
            [
                "Limit distribution within organization",
                "Follow internal sharing guidelines",
            ]
        )
    elif "PUBLIC" in security_upper or (
        "OFFICIAL" in security_upper and "OPEN" in security_upper
    ):
        recommendations.extend(
            [
                "May be shared publicly as appropriate",
                "Follow standard information sharing practices",
            ]
        )

    if "HIGH" in sensitivity_upper:
        recommendations.append("Exercise extra caution in handling and sharing")
    elif "MEDIUM" in sensitivity_upper:
        recommendations.append("Apply standard sensitivity controls")

    return recommendations
