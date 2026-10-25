"""
Pydantic schemas for Client dashboard and personal account operations.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, model_validator

from app.security.passwords import validate_password_strength


class ClientOverviewResponse(BaseModel):
    user_id: str
    username: str
    email: str
    role: str
    is_active: bool
    created_at: datetime
    active_targets_count: int = 0
    scans_completed_count: int = 0
    pending_fixes_count: int = 0
    security_shield_status: str = "Active"
    php2shell_protected: bool = True
    notice: str = "Target management will be introduced in Phase 4; background scanner queue in Phase 5."


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., min_length=1, description="Current account password")
    new_password: str = Field(..., min_length=8, max_length=128, description="New secure password")
    new_password_confirmation: str = Field(..., min_length=8, max_length=128, description="Confirm new password")

    @model_validator(mode="after")
    def validate_new_password(self) -> "ChangePasswordRequest":
        if self.new_password != self.new_password_confirmation:
            raise ValueError("New password confirmation does not match the entered password.")

        is_valid, error = validate_password_strength(self.new_password)
        if not is_valid and error:
            raise ValueError(error)

        return self
