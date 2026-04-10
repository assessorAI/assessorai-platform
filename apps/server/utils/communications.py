from __future__ import annotations

import logging
from typing import Iterable, Optional, Dict, Any, Sequence

from sqlalchemy.orm import Session

from ..db.models import User as UserORM, Mandato as MandatoORM
from ..services import get_email_service

logger = logging.getLogger(__name__)


def _ensure_sequence(value: Iterable[str]) -> Sequence[str]:
    return [item for item in value if item]


def send_email_to_user(
    user: UserORM,
    subject: str,
    message: Optional[str] = None,
    *,
    template_name: Optional[str] = None,
    template_context: Optional[Dict[str, Any]] = None,
) -> Optional[int]:
    if not user or not user.email:
        logger.warning("Cannot send email, user or user.email missing.")
        return None
    service = get_email_service()
    return service.send_email(
        recipients=user.email,
        subject=subject,
        message=message,
        template_name=template_name,
        template_context=template_context,
    )


def send_email_to_user_by_id(
    session: Session,
    user_id: int,
    subject: str,
    message: Optional[str] = None,
    *,
    template_name: Optional[str] = None,
    template_context: Optional[Dict[str, Any]] = None,
) -> Optional[int]:
    user = session.get(UserORM, user_id)
    if not user:
        logger.warning("Cannot send email, user with id=%s not found.", user_id)
        return None
    return send_email_to_user(
        user,
        subject,
        message,
        template_name=template_name,
        template_context=template_context,
    )


def send_email_to_mandato(
    mandato: MandatoORM,
    subject: str,
    message: Optional[str] = None,
    *,
    template_name: Optional[str] = None,
    template_context: Optional[Dict[str, Any]] = None,
) -> Optional[int]:
    if not mandato:
        logger.warning("Cannot send email, mandato missing.")
        return None
    recipient_emails = {user.email for user in mandato.users if getattr(user, "email", None)}
    if not recipient_emails:
        logger.warning("Mandato id=%s has no users with email addresses.", getattr(mandato, "id", None))
        return None
    service = get_email_service()
    return service.send_email(
        recipients=_ensure_sequence(recipient_emails),
        subject=subject,
        message=message,
        template_name=template_name,
        template_context=template_context,
    )


def send_email_to_mandato_by_id(
    session: Session,
    mandato_id: int,
    subject: str,
    message: Optional[str] = None,
    *,
    template_name: Optional[str] = None,
    template_context: Optional[Dict[str, Any]] = None,
) -> Optional[int]:
    mandato = session.get(MandatoORM, mandato_id)
    if not mandato:
        logger.warning("Cannot send email, mandato with id=%s not found.", mandato_id)
        return None
    return send_email_to_mandato(
        mandato,
        subject,
        message,
        template_name=template_name,
        template_context=template_context,
    )


def send_email_to_recipients(
    emails: Iterable[str],
    subject: str,
    message: Optional[str] = None,
    *,
    template_name: Optional[str] = None,
    template_context: Optional[Dict[str, Any]] = None,
) -> Optional[int]:
    targets = [email for email in emails if email]
    if not targets:
        logger.warning("No valid email addresses provided.")
        return None
    service = get_email_service()
    return service.send_email(
        recipients=targets,
        subject=subject,
        message=message,
        template_name=template_name,
        template_context=template_context,
    )
