from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Iterable, Optional, Sequence, Union, Dict, Any

from markdown import markdown

try:
    from langchain_core.prompts import PromptTemplate
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail, Email
except ImportError:  # pragma: no cover - handled via graceful degradation
    SendGridAPIClient = None  # type: ignore[assignment]
    Mail = None  # type: ignore[assignment]
    Email = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)

DEFAULT_TEMPLATE_DIR = Path(__file__).resolve().parent / "templates" / "emails"


class EmailTemplateRenderer:
    """Load and render markdown templates from disk."""

    def __init__(self, base_dir: Optional[Path] = None) -> None:
        env_dir = os.getenv("EMAIL_TEMPLATE_DIR")
        if env_dir:
            base_dir = Path(env_dir)
        self.base_dir = Path(base_dir) if base_dir is not None else DEFAULT_TEMPLATE_DIR

    def _resolve_template(self, template_name: str) -> Path:
        path = Path(template_name)
        if not path.is_absolute():
            path = self.base_dir / path
        if path.suffix == "":
            path = path.with_suffix(".md")
        if not path.exists():
            raise FileNotFoundError(f"Template '{template_name}' not found at {path}")
        return path

    def render_markdown(self, template_name: str, context: Optional[Dict[str, Any]] = None) -> str:
        path = self._resolve_template(template_name)
        content = path.read_text(encoding="utf-8")
        if context:
            try:
                template = PromptTemplate.from_template(content, template_format="mustache")
                content = template.format(**context)
            except KeyError as exc:
                missing_key = exc.args[0]
                raise ValueError(f"Missing key '{missing_key}' in template context for '{template_name}'") from exc
        return content

    @staticmethod
    def markdown_to_html(source: str) -> str:
        return markdown(source)


class SendGridEmailService:
    """Wrapper around SendGrid to simplify sending communications."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        sender_email: Optional[str] = None,
        sender_name: Optional[str] = None,
        template_renderer: Optional[EmailTemplateRenderer] = None,
    ) -> None:
        self.api_key = api_key or os.getenv("SENDGRID_API_KEY")
        self.sender_email = sender_email or os.getenv("SENDGRID_SENDER_EMAIL")
        self.sender_name = sender_name or os.getenv("SENDGRID_SENDER_NAME")
        self.template_renderer = template_renderer or EmailTemplateRenderer()

        self._client: Optional[SendGridAPIClient] = None
        if SendGridAPIClient is None:
            logger.warning("sendgrid package not installed; email sending disabled.")
        elif self.api_key:
            try:
                self._client = SendGridAPIClient(self.api_key)
            except Exception:
                logger.exception("Failed to initialise SendGrid client")
        else:
            logger.warning("SENDGRID_API_KEY not configured; email sending disabled.")

    @property
    def is_configured(self) -> bool:
        return bool(self._client and self.sender_email)

    def _normalise_recipients(self, recipients: Union[str, Iterable[str]]) -> Sequence[str]:
        if isinstance(recipients, str):
            recipients_iter = [recipients]
        else:
            recipients_iter = list(recipients)
        unique = []
        for email in recipients_iter:
            if not email:
                continue
            lowered = email.strip()
            if lowered and lowered not in unique:
                unique.append(lowered)
        return unique

    def _build_mail(
        self,
        recipients: Sequence[str],
        subject: str,
        plain_body: str,
        html_body: Optional[str] = None,
    ) -> Mail:
        if Mail is None or Email is None:
            raise RuntimeError("SendGrid helpers not available; install the 'sendgrid' package.")
        from_email = Email(self.sender_email, self.sender_name)  # type: ignore[arg-type]
        mail = Mail(
            from_email=from_email,
            to_emails=list(recipients),
            subject=subject,
            plain_text_content=plain_body,
            html_content=html_body,
        )
        return mail

    def send_email(
        self,
        recipients: Union[str, Iterable[str]],
        subject: str,
        message: Optional[str] = None,
        *,
        template_name: Optional[str] = None,
        template_context: Optional[Dict[str, Any]] = None,
        render_markdown: bool = True,
    ) -> Optional[int]:
        if not self.is_configured:
            logger.error("Attempted to send email without SendGrid configuration.")
            return None

        normalised_recipients = self._normalise_recipients(recipients)
        if not normalised_recipients:
            logger.warning("No valid recipients provided for email with subject '%s'", subject)
            return None

        if template_name:
            markdown_body = self.template_renderer.render_markdown(template_name, template_context)
        elif message:
            markdown_body = message
        else:
            raise ValueError("Either 'message' or 'template_name' must be provided.")

        html_body = self.template_renderer.markdown_to_html(markdown_body) if render_markdown else markdown_body
        plain_body = markdown_body if render_markdown else (message or "")

        mail = self._build_mail(normalised_recipients, subject, plain_body, html_body)

        try:
            response = self._client.send(mail)  # type: ignore[union-attr]
        except Exception:
            logger.exception("Failed to send email via SendGrid.")
            return None

        logger.info(
            "Email sent via SendGrid. Status: %s; Subject: '%s'; Recipients: %s",
            getattr(response, "status_code", "unknown"),
            subject,
            normalised_recipients,
        )
        return getattr(response, "status_code", None)


_singleton_service: Optional[SendGridEmailService] = None


def get_email_service() -> SendGridEmailService:
    global _singleton_service
    if _singleton_service is None:
        _singleton_service = SendGridEmailService()
    return _singleton_service
