"""
Pydantic schemas for Website Target Registration, Ownership Verification, and Scan Authorization.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

from app.models.website import VerificationMethod, VerificationStatus
from app.security.url_validator import validate_and_normalize_target_url


class CreateWebsiteRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, description="Friendly site label, e.g. Production Portal")
    target_url: str = Field(..., min_length=4, max_length=500, description="Target domain or base URL")
    verification_method: VerificationMethod = Field(
        default=VerificationMethod.FILE,
        description="Chosen ownership verification technique",
    )

    @field_validator("name")
    @classmethod
    def clean_name(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Website name cannot be blank.")
        return trimmed

    @field_validator("target_url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        normalized, _ = validate_and_normalize_target_url(v)
        return normalized


class UpdateVerificationMethodRequest(BaseModel):
    verification_method: VerificationMethod


class ScanAuthorizationRequest(BaseModel):
    authorized_by_name: str = Field(..., min_length=2, max_length=100, description="Full legal name of the authorizing party")
    authorized_by_email: str = Field(..., min_length=5, max_length=255, description="Authorized contact email")
    legal_confirmation: bool = Field(
        ...,
        description="Explicit warrant that user owns or has legal written permission to scan the target",
    )
    allowed_scan_types: str = Field(
        default="passive,owasp_standard",
        description="Comma-separated authorized assessment categories",
    )

    @field_validator("authorized_by_email")
    @classmethod
    def clean_email(cls, v: str) -> str:
        return v.strip().lower()

    @model_validator(mode="after")
    def require_legal_confirmation(self) -> "ScanAuthorizationRequest":
        if not self.legal_confirmation:
            raise ValueError("You must explicitly confirm that you own or have legal authorization to assess this target.")
        return self


class RevokeAuthorizationRequest(BaseModel):
    revocation_reason: Optional[str] = Field(None, max_length=500, description="Optional explanation for revoking scan authorization")


class ScanAuthorizationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    website_id: str
    is_authorized: bool
    authorized_by_name: str
    authorized_by_email: str
    legal_confirmation: bool
    allowed_scan_types: str
    authorized_at: Optional[datetime]
    expires_at: Optional[datetime]
    is_revoked: bool
    revoked_at: Optional[datetime]
    revocation_reason: Optional[str]


class VerificationInstructions(BaseModel):
    method: str
    token: str
    file_path: Optional[str] = None
    file_content: Optional[str] = None
    meta_tag_snippet: Optional[str] = None
    dns_record_name: Optional[str] = None
    dns_txt_value: Optional[str] = None


class WebsiteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    name: str
    target_url: str
    domain: str
    verification_method: str
    verification_token: str
    verification_status: str
    verified_at: Optional[datetime]
    last_verification_attempt: Optional[datetime]
    verification_error: Optional[str]
    is_suspended_by_admin: bool
    suspension_reason: Optional[str]
    created_at: datetime
    authorization: Optional[ScanAuthorizationResponse] = None
    instructions: Optional[VerificationInstructions] = None


class VerificationResultResponse(BaseModel):
    is_verified: bool
    verification_status: str
    message: str
    verified_at: Optional[datetime] = None


class AdminSuspendWebsiteRequest(BaseModel):
    is_suspended: bool
    suspension_reason: Optional[str] = Field(None, max_length=500)
