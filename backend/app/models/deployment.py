"""SQLAlchemy models for Source-Code Integration, Git Pull Requests, Staging, and Secure Deployment."""
from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class DeploymentEnvironment(str, enum.Enum):
    STAGING = "staging"
    PRODUCTION = "production"
    GIT_PR_ONLY = "git_pr_only"


class DeploymentStatus(str, enum.Enum):
    PENDING = "pending"
    PR_CREATED = "pr_created"
    STAGED = "staged"
    VERIFYING = "verifying"
    DEPLOYED = "deployed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class RepositoryProvider(str, enum.Enum):
    GITHUB = "github"
    GITLAB = "gitlab"
    LOCAL_GIT = "local_git"


class RepositoryConnection(Base):
    __tablename__ = "repository_connections"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    website_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("websites.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    provider: Mapped[str] = mapped_column(
        String(50),
        default=RepositoryProvider.GITHUB.value,
        nullable=False,
    )
    repo_name: Mapped[str] = mapped_column(
        String(255),  # e.g. "acme-corp/storefront-php"
        nullable=False,
    )
    default_branch: Mapped[str] = mapped_column(
        String(100),
        default="main",
        nullable=False,
    )
    masked_token: Mapped[str] = mapped_column(
        String(100),  # e.g. "ghp_***4a2b"
        nullable=False,
    )
    encrypted_token: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship("User", backref="repository_connections")
    website: Mapped[Optional["Website"]] = relationship("Website", backref="repository_connections")


class DeploymentTarget(Base):
    __tablename__ = "deployment_targets"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    website_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("websites.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    environment: Mapped[str] = mapped_column(
        String(30),
        default=DeploymentEnvironment.STAGING.value,
        nullable=False,
    )
    target_type: Mapped[str] = mapped_column(
        String(50),
        default="github_pr",  # github_pr | webhook | staging_cluster
        nullable=False,
    )
    endpoint_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )
    is_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=False,  # STRICT: Disabled by default
        nullable=False,
    )
    health_check_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    user: Mapped["User"] = relationship("User", backref="deployment_targets")
    website: Mapped["Website"] = relationship("Website", backref="deployment_targets")


class DeploymentRecord(Base):
    __tablename__ = "deployment_records"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    session_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("remediation_sessions.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    target_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("deployment_targets.id", ondelete="SET NULL"),
        nullable=True,
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    website_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("websites.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    environment: Mapped[str] = mapped_column(
        String(30),
        default=DeploymentEnvironment.STAGING.value,
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(30),
        default=DeploymentStatus.PENDING.value,
        index=True,
        nullable=False,
    )

    # Git Integration details
    git_branch: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    git_commit_sha: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
    )
    pull_request_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )
    pull_request_number: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )

    # Safety checks
    pre_deployment_test_status: Mapped[str] = mapped_column(
        String(30),
        default="passed",
        nullable=False,
    )
    client_approved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    client_notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    deployed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Rollback snapshot for defense-in-depth safety
    rollback_snapshot: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    rollback_executed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    rollback_reason: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    audit_trail: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    session: Mapped["RemediationSession"] = relationship("RemediationSession", backref="deployments")
    target: Mapped[Optional["DeploymentTarget"]] = relationship("DeploymentTarget", backref="deployments")
    user: Mapped["User"] = relationship("User", backref="deployments")
    website: Mapped["Website"] = relationship("Website", backref="deployments")
