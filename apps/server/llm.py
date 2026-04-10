import os
import base64
import logging
import re

from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_google_vertexai import ChatVertexAI

from langchain_core.messages import HumanMessage

from pydantic import BaseModel
from typing import Any, cast, Optional

from fastapi.responses import JSONResponse, StreamingResponse
from .models import BaseStructuredAnswer

logger = logging.getLogger(__name__)


def extract_mustache_variables(template_content: str) -> set[str]:
    """
    Extract all Mustache variables from template content.
    
    Matches {{variable}} but ignores conditionals like {{#variable}}, {{/variable}}, {{^variable}}.
    Returns root-level variable names only (e.g., 'mandato' from '{{mandato.nome}}').
    
    Args:
        template_content: Markdown template with Mustache syntax
        
    Returns:
        Set of root-level variable names
        
    Example:
        >>> extract_mustache_variables("Hello {{name}}, you work at {{company.name}}")
        {'name', 'company'}
    """
    # Match {{variable}} but not {{#variable}} or {{/variable}} or {{^variable}}
    pattern = r'\{\{(?![#/^])([a-zA-Z_][a-zA-Z0-9_\.]*)\}\}'
    matches = re.findall(pattern, template_content)
    # Return root-level variables only (before any dots)
    return {match.split('.')[0] for match in matches}


def apply_defaults_to_template(
    prompt: ChatPromptTemplate, 
    content: dict
) -> ChatPromptTemplate:
    """
    Apply empty string defaults to template variables missing from content.
    
    Uses LangChain's built-in partial() method to inject defaults for any
    template variables not provided in the content dictionary. This prevents
    validation errors when invoking the prompt.
    
    Args:
        prompt: ChatPromptTemplate with Mustache variables
        content: Dictionary of variables provided by caller
        
    Returns:
        ChatPromptTemplate with missing variables filled with empty strings
        
    Example:
        >>> template = ChatPromptTemplate.from_messages([
        ...     ("system", "Hello {{name}} from {{city}}")
        ... ], template_format="mustache")
        >>> content = {"name": "John"}
        >>> template_with_defaults = apply_defaults_to_template(template, content)
        >>> # Now template only requires 'name', 'city' defaults to ""
    """
    required_vars = set(prompt.input_variables)
    provided_vars = set(content.keys())
    missing_vars = required_vars - provided_vars
    
    if missing_vars:
        defaults = {var: "" for var in missing_vars}
        logger.info(
            f"Applying empty defaults for missing template variables",
            extra={"missing_variables": sorted(missing_vars), "provided_variables": sorted(provided_vars)}
        )
        return prompt.partial(**defaults)
    
    return prompt


def load_prompt(prompt_template: str, session: Optional[Any] = None) -> str:
    """
    Load prompt template with fallback logic:
    1. Try database (default active version)
    2. Fall back to prompts/{template}.md file
    3. Raise ValueError if neither exists
    
    Args:
        prompt_template: Template identifier (e.g., 'generate_oficio')
        session: Optional SQLAlchemy session for database lookup
    
    Returns:
        str: Template content in Markdown/Mustache format
    
    Raises:
        ValueError: If template not found in database or filesystem
    """
    # Try database first if session provided
    if session:
        try:
            from .db.models import PromptTemplate
            db_template = session.query(PromptTemplate).filter(
                PromptTemplate.template_type == prompt_template,
                PromptTemplate.is_default == True,
                PromptTemplate.is_active == True
            ).first()
            
            if db_template:
                logger.info(
                    f"Loaded prompt '{prompt_template}' from database",
                    extra={"template_type": prompt_template, "version": db_template.version}
                )
                return db_template.content
        except Exception as e:
            logger.warning(
                f"Failed to load prompt from database, falling back to file",
                extra={"template_type": prompt_template, "error": str(e)}
            )
    
    # Fallback to file
    file_path = f'prompts/{prompt_template}.md'
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        logger.info(
            f"Loaded prompt '{prompt_template}' from file (fallback)",
            extra={"template_type": prompt_template, "source": "file"}
        )
        return content
    
    raise ValueError(f"Prompt template '{prompt_template}' not found in database or filesystem")

    
def call_llm_with_template_content(content: dict, template_content: str, files: list = [],
             answer_template: type[BaseModel] = BaseStructuredAnswer,
             session: Optional[Any] = None) -> dict:
    """
    Call LLM with explicit template content instead of loading from database/file.
    Used for evaluation runs to test specific template versions.
    """
    prompt = ChatPromptTemplate.from_messages([
        ("system", template_content),
        ], template_format="mustache")
    
    # Apply empty defaults for any missing template variables
    prompt = apply_defaults_to_template(prompt, content)
    
    if "input" in content:
        prompt.messages.append(HumanMessage([content["input"]]))
    if isinstance(content, dict) and content.get("references_text"):
        for txt in content["references_text"]:
            prompt.messages.append(HumanMessage([str(txt)]))

    def add_file(chat_template_obj):
        for file in files:
            if file["type"] == "remote" and file["path"].startswith("gs://"):
                file["filename"] = file["path"].split("/")[-1]
                new_file = {
                    "type": "media",
                    "file_uri": file["path"],
                    "mime_type": "application/pdf",
                }
            elif file["type"] == "local":
                pdf_base64 = base64.b64encode(file["raw"]).decode("utf-8")
                new_file = {
                            "type": "media",
                            "data": pdf_base64,
                            "mime_type": "application/pdf",
                        }
            else:
                raise ValueError("Unsupported file type")
            file_human_message = HumanMessage([file["filename"], new_file])
            chat_template_obj.messages.append(file_human_message)
                
        return chat_template_obj
            
    llm = ChatVertexAI(
        model="gemini-2.0-flash",
        temperature=0,
        max_tokens=None,
        max_retries=2,
    )
    
    chain = prompt | add_file | llm.with_structured_output(answer_template)
    response = cast(BaseModel, chain.invoke(content))
    return response.model_dump()


def call_llm(content: dict, prompt_template: str, files: list = [],
             answer_template: type[BaseModel] = BaseStructuredAnswer,
             session: Optional[Any] = None) -> dict:
    system_prompt = load_prompt(prompt_template, session=session)
    return call_llm_with_template_content(content, system_prompt, files, answer_template, session)

def generate_response(content: dict | str, format: str | None = None):
    fmt = format.lower() if isinstance(format, str) else None
    if fmt == 'pdf':
        from .utils import converters as _converters
        text = content if isinstance(content, str) else str(content)
        file_pdf = _converters.convert2pdf(text)
        return StreamingResponse(
            file_pdf,
            media_type='application/pdf',
            headers={"Content-Disposition": "attachment; filename=oficio.pdf"}
        )
    elif fmt == 'docx':
        from .utils import converters as _converters
        text = content if isinstance(content, str) else str(content)
        file_docx = _converters.convert2docx(text)
        return StreamingResponse(
            file_docx,
            media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            headers={"Content-Disposition": "attachment; filename=oficio.docx"}
        )
    else:
        return JSONResponse(content)
