from __future__ import annotations

from datetime import timedelta, datetime, timezone
import os
import secrets
from typing import List, Optional
from pydantic import BaseModel, EmailStr

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from ..db.session import get_session
from ..db.models import User as UserORM, PasswordResetToken as PasswordResetTokenORM
from ..models import AdminDashboardSummary, AdminHealthResponse
from ..services.admin_dashboard import collect_dashboard_summary, collect_health_snapshot
from ..services.sendgrid_service import get_email_service
from ..utils.config import get_frontend_url
from .deps import require_admin_user


def utc_now_naive() -> datetime:
    """Returns current UTC time as naive datetime for database storage."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def extract_subject_from_template(template_name: str) -> Optional[str]:
    """
    Extract subject line from email template if it starts with # TITLE.
    Returns the title without the # prefix, or None if not found.
    """
    template_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "services", "templates", "emails", template_name
    )
    
    try:
        with open(template_path, "r", encoding="utf-8") as f:
            first_line = f.readline().strip()
            if first_line.startswith("#"):
                return first_line.lstrip("#").strip()
    except Exception:
        pass
    
    return None

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
)


@router.get("/summary", response_model=AdminDashboardSummary)
def get_admin_summary(
    session: Session = Depends(get_session),
    current_admin= require_admin_user,
):
    return collect_dashboard_summary(session)


@router.get("/health", response_model=AdminHealthResponse)
def get_admin_health(
    session: Session = Depends(get_session),
    current_admin= require_admin_user,
):
    return collect_health_snapshot(session)


class SendPasswordResetRequest(BaseModel):
    """Request to send password reset emails to one or more users"""
    user_ids: Optional[List[int]] = None  # Specific user IDs
    emails: Optional[List[str]] = None  # Specific emails, or ["all"] to send to ALL users
    template: Optional[str] = "password_reset"  # Email template: password_reset or bubble_import_password_reset


class SendPasswordResetResponse(BaseModel):
    """Response with statistics about sent emails"""
    sent: int
    failed: int
    skipped: int
    details: List[dict]


@router.post("/send-password-reset", response_model=SendPasswordResetResponse)
def send_password_reset_emails(
    payload: SendPasswordResetRequest,
    session: Session = Depends(get_session),
    current_admin= require_admin_user,
):
    """
    Send password reset emails to specified users.
    
    - If user_ids is provided, send to those specific user IDs
    - If emails is provided with ["all"], send to ALL active users
    - If emails is provided with specific emails, send to those emails only
    - If both user_ids and emails are None, return error (no users selected)
    - template: "password_reset" (default) or "bubble_import_password_reset"
    """
    email_service = get_email_service()
    
    if not email_service.is_configured:
        raise HTTPException(
            status_code=503,
            detail="Email service not configured. Please configure SendGrid API key."
        )
    
    # Check if nothing was specified
    if not payload.user_ids and not payload.emails:
        raise HTTPException(
            status_code=400,
            detail="No users specified. Provide user_ids, emails, or emails=['all'] to send to all users."
        )
    
    # Determine which users to send to
    users_query = select(UserORM).where(UserORM.is_active == True)
    send_to_all = False
    
    if payload.emails and len(payload.emails) == 1 and payload.emails[0].lower() == "all":
        # Special case: send to ALL active users
        send_to_all = True
        # No additional filter needed - already filtering by is_active
    elif payload.user_ids:
        # Send to specific user IDs
        users_query = users_query.where(UserORM.id.in_(payload.user_ids))
    elif payload.emails:
        # Send to specific emails (case-insensitive comparison)
        emails_lower = [e.lower() for e in payload.emails]
        users_query = users_query.where(func.lower(UserORM.email).in_(emails_lower))
    
    users = session.scalars(users_query).all()
    
    if not users:
        return SendPasswordResetResponse(
            sent=0,
            failed=0,
            skipped=0,
            details=[{"message": "No users found matching criteria"}]
        )
    
    frontend_url = get_frontend_url()
    sent = 0
    failed = 0
    skipped = 0
    details = []
    
    for user in users:
        try:
            # Generate reset token
            token_str = secrets.token_urlsafe(32)
            expires = timedelta(hours=24)
            
            reset_token = PasswordResetTokenORM(
                token=token_str,
                user_id=user.id,
                expires_at=utc_now_naive() + expires,
                used=False
            )
            session.add(reset_token)
            session.flush()
            
            # Prepare reset link
            reset_link = f"{frontend_url}/reset-password?token={token_str}"
            
            # Determine template name
            template_name = f"{payload.template or 'password_reset'}.md"
            
            # Extract subject from template or use default
            subject = extract_subject_from_template(template_name) or "Redefinição de Senha - AssessorAI"
            
            # Send email
            status_code = email_service.send_email(
                recipients=user.email,
                subject=subject,
                template_name=template_name,
                template_context={
                    "first_name": user.first_name or "Usuário",
                    "reset_link": reset_link
                }
            )
            
            if status_code and 200 <= status_code < 300:
                sent += 1
                details.append({
                    "email": user.email,
                    "status": "sent",
                    "user_id": user.id
                })
            else:
                failed += 1
                details.append({
                    "email": user.email,
                    "status": "failed",
                    "user_id": user.id,
                    "error": f"Email service returned status {status_code}"
                })
        
        except Exception as e:
            failed += 1
            details.append({
                "email": user.email,
                "status": "failed",
                "user_id": user.id,
                "error": str(e)
            })
    
    session.commit()
    
    return SendPasswordResetResponse(
        sent=sent,
        failed=failed,
        skipped=skipped,
        details=details
    )
