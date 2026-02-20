"""Audit logging service for tracking user actions."""

import logging
import uuid

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog

logger = logging.getLogger(__name__)


async def log_action(
    db: AsyncSession,
    *,
    clinic_id: uuid.UUID,
    user_id: uuid.UUID | None = None,
    action: str,
    resource_type: str,
    resource_id: str | None = None,
    description: str | None = None,
    changes: dict | None = None,
    request: Request | None = None,
) -> AuditLog:
    """Create an audit log entry."""
    ip_address = None
    user_agent = None
    if request:
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent", "")[:500]

    entry = AuditLog(
        clinic_id=clinic_id,
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=str(resource_id) if resource_id else None,
        description=description,
        changes=changes,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.add(entry)
    return entry
