"""
Pydantic schemas for Administrative operations and system overview.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.schemas.auth import UserResponse


class SystemServiceStatus(BaseModel):
    name: str
    status: str
    details: str
    is_operational: bool


class AdminOverviewResponse(BaseModel):
    total_users: int
    total_clients: int
    total_admins: int
    active_users: int
    disabled_users: int
    system_status: str  # "healthy" | "degraded"
    services: List[SystemServiceStatus]
    security_shields: Dict[str, Any]


class UpdateUserStatusRequest(BaseModel):
    is_active: bool = Field(..., description="Set user active status")


class AuditEvent(BaseModel):
    id: str
    event_type: str
    description: str
    severity: str  # "info" | "warning" | "critical"
    actor: str
    timestamp: datetime


class AdminAuditResponse(BaseModel):
    total_events: int
    events: List[AuditEvent]
