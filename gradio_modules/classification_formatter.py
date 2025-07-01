#!/usr/bin/env python3
"""
Enhanced classification response formatting for better user experience.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime


def format_classification_response(
    classification: Dict[str, Any],
    extraction_info: Dict[str, Any],
    file_info: Dict[str, str],
) -> Dict[str, str]:
    """
    Format classification response with enhanced presentation.

    Args:
        classification: Classification results from the model
        extraction_info: Information about content extraction
        file_info: Basic file information

    Returns:
        Dict with formatted strings for display
    """

    # Get classification details
    security_class = classification.get("classification", "Unknown")
    sensitivity = classification.get("sensitivity", "Unknown")
    reasoning = classification.get("reasoning", "No reasoning provided")
    confidence = classification.get("confidence", None)

    # Format security classification with emoji and styling
    security_formatted = format_security_classification(security_class)

    # Format sensitivity with appropriate styling
    sensitivity_formatted = format_sensitivity_level(sensitivity)

    # Format file information with extraction details
    file_info_formatted = format_file_information(file_info, extraction_info)

    # Format reasoning with better structure
    reasoning_formatted = format_reasoning(reasoning, confidence)

    # Create summary section
    summary_formatted = format_classification_summary(
        security_class, sensitivity, confidence, extraction_info
    )

    return {
        "classification": security_formatted,
        "sensitivity": sensitivity_formatted,
        "file_info": file_info_formatted,
        "reasoning": reasoning_formatted,
        "summary": summary_formatted,
    }


def format_security_classification(classification: str) -> str:
    """Format security classification with appropriate styling."""

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
    """Format sensitivity level with appropriate styling."""

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

    normalized = sensitivity.upper().strip()
    formatted = sensitivity_mapping.get(normalized, f"⚪ **{sensitivity.upper()}**")

    return formatted


def format_file_information(
    file_info: Dict[str, str], extraction_info: Dict[str, Any]
) -> str:
    """Format file information with extraction details."""

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
    """Format extraction method with descriptive text."""

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
    """Format file size in human-readable format."""

    if size_bytes < 1024:
        return f"{size_bytes} bytes"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


def format_reasoning(reasoning: str, confidence: Optional[float] = None) -> str:
    """Format classification reasoning with better structure."""

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
    """Create a formatted summary of the classification."""

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
    """Get handling recommendations based on classification."""

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
