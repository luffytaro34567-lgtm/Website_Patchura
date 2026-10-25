"""Pydantic schemas for Authentication and User management."""
from __future__ import annotations

import re
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

from app.models.user import UserRole
from app.security.passwords import validate_password_strength


class UserRegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="Unique account username")
    email: str = Field(..., min_length=5, max_length=255, description="Valid user email address")
    password: str = Field(..., min_length=8, max_length=128, description="Account password")
    password_confirmation: str = Field(..., min_length=8, max_length=128, description="Password confirmation")

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        trimmed = v.strip()
        if not re.match(r"^[a-zA-Z0-9_\-]+$", trimmed):
            raise ValueError("Username may only contain letters, numbers, hyphens, and underscores.")
        return trimmed

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        cleaned = v.strip().lower()
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", cleaned):
            raise ValueError("A valid email address is required.")
        return cleaned

    @model_validator(mode="after")
    def validate_passwords(self) -> "UserRegisterRequest":
        if self.password != self.password_confirmation:
            raise ValueError("Password confirmation does not match the entered password.")

        is_valid, error_msg = validate_password_strength(self.password)
        if not is_valid and error_msg:
            raise ValueError(error_msg)

        return self


class UserLoginRequest(BaseModel):
    login: str = Field(..., min_length=1, max_length=255, description="Username or email address")
    password: str = Field(..., min_length=1, max_length=128, description="User password")

    @field_validator("login")
    @classmethod
    def clean_login(cls, v: str) -> str:
        return v.strip().lower()


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., min_length=20, description="Rotating refresh token secret")


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    username: str
    email: str
    role: str
    is_active: bool
    created_at: datetime


class AuthTokensResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_token: str
    user: UserResponse


class AdminCreateUserRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., min_length=5, max_length=255)
    password: str = Field(..., min_length=8, max_length=128)
    role: UserRole = Field(default=UserRole.CLIENT)
    is_active: bool = Field(default=True)

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        trimmed = v.strip()
        if not re.match(r"^[a-zA-Z0-9_\-]+$", trimmed):
            raise ValueError("Username may only contain letters, numbers, hyphens, and underscores.")
        return trimmed

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        cleaned = v.strip().lower()
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", cleaned):
            raise ValueError("A valid email address is required.")
        return cleaned

    @model_validator(mode="after")
    def validate_password_policy(self) -> "AdminCreateUserRequest":
        is_valid, error_msg = validate_password_strength(self.password)
        if not is_valid and error_msg:
            raise ValueError(error_msg)
        return self


class PasswordRecoveryRequest(BaseModel):
    email: str = Field(..., description="Registered account email address")

    @field_validator("email")
    @classmethod
    def clean_email(cls, v: str) -> str:
        return v.strip().lower()


class PasswordResetConfirmRequest(BaseModel):
    token: str = Field(..., min_length=10, description="Password recovery token")
    new_password: str = Field(..., min_length=8, max_length=128, description="New password")
    new_password_confirmation: Optional[str] = Field(None, min_length=8, max_length=128, description="Confirmation password")
    confirm_password: Optional[str] = Field(None, min_length=8, max_length=128, description="Confirmation password alias")

    @model_validator(mode="after")
    def validate_password_match(self) -> "PasswordResetConfirmRequest":
        confirm = self.new_password_confirmation or self.confirm_password
        if not confirm:
            raise ValueError("Password confirmation is required.")
        if self.new_password != confirm:
            raise ValueError("Password confirmation does not match the entered password.")
        self.new_password_confirmation = confirm
        is_valid, error_msg = validate_password_strength(self.new_password)
        if not is_valid and error_msg:
            raise ValueError(error_msg)
        return self
