"""
Text cleanup utilities for LLM responses.

Handles removal of redundant headers that LLMs sometimes add to structured outputs.
"""
import re
from typing import Optional


def remove_redundant_title(field_name: str, text: str) -> str:
    """
    Remove redundant title from the beginning of text field.
    
    Handles various title formats:
    - Markdown headers: # TITLE, ## TITLE, ### TITLE
    - Bold markdown: **TITLE**
    - Plain text: TITLE
    
    Only removes titles at the very beginning of the text that match the field name.
    If the line contains more content after the title, keeps the rest of the line.
    
    Args:
        field_name: Name of the field (e.g., "justificativa", "texto", "ementa")
        text: The full text content that may contain a redundant title
        
    Returns:
        Cleaned text with redundant title removed
        
    Examples:
        >>> remove_redundant_title("justificativa", "**JUSTIFICATIVA**\\n\\nTexto aqui")
        "Texto aqui"
        
        >>> remove_redundant_title("texto", "# TEXTO\\n\\nConteúdo")
        "Conteúdo"
        
        >>> remove_redundant_title("ementa", "EMENTA: Este projeto...")
        "Este projeto..."
        
        >>> remove_redundant_title("parecer", "Normal text")
        "Normal text"
    """
    if not text or not text.strip():
        return text
    
    # Normalize field name for comparison (uppercase, no special chars)
    normalized_field = field_name.upper().strip()
    
    # Build regex pattern to match title at start of text
    # Matches:
    # - Optional markdown headers (##, ###)
    # - Optional bold markers (**)
    # - The field name (case insensitive)
    # - Optional bold closing (**)
    # - Optional punctuation (:, -, etc.)
    # - Optional whitespace
    # Captures any remaining text on the same line
    pattern = rf'^(\s*)(\#+\s*)?(\**)?\s*{re.escape(normalized_field)}\s*(\**)?\s*[:;\-]?\s*(.*?)(?:\n|$)'
    
    match = re.match(pattern, text, re.IGNORECASE | re.MULTILINE)
    
    if match:
        # Get any text after the title on the same line
        remaining_on_line = match.group(5).strip()
        
        # Get text after the matched line
        rest_of_text = text[match.end():].lstrip()
        
        # Combine remaining text
        if remaining_on_line:
            # Title had more content on the same line - keep it
            cleaned = remaining_on_line
            if rest_of_text:
                cleaned += '\n\n' + rest_of_text
        else:
            # Title was on its own line - just use the rest
            cleaned = rest_of_text
        
        return cleaned
    
    # No redundant title found
    return text


def clean_llm_response(response: dict, fields_to_clean: list[str]) -> dict:
    """
    Clean multiple fields in an LLM response dict.
    
    Args:
        response: Dictionary containing LLM response fields
        fields_to_clean: List of field names to clean (e.g., ["justificativa", "texto"])
        
    Returns:
        Response dict with cleaned fields
        
    Example:
        >>> response = {"titulo": "Project", "justificativa": "**JUSTIFICATIVA**\n\nText here"}
        >>> clean_llm_response(response, ["justificativa"])
        {"titulo": "Project", "justificativa": "Text here"}
    """
    cleaned = response.copy()
    
    for field_name in fields_to_clean:
        if field_name in cleaned and isinstance(cleaned[field_name], str):
            cleaned[field_name] = remove_redundant_title(field_name, cleaned[field_name])
    
    return cleaned
