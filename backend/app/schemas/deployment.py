"""Pydantic schemas for Source-Code Integration, Pull Requests, Staging, and Deployment."""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class CreateRepositoryConnectionRequest(BaseModel):
    website_id: Optional[str] = Field(default=None, description="Optional website to link this repository to")
    provider: str = Field(default="github", description="'github', 'gitlab', or 'local_git'")
    repo_name: str = Field(..., min_length=3, max_length=255, description="Repository identifier (e.g. 'owner/repo')")
    default_branch: str = Field(default="main", description="Protected base branch name (e.g. 'main' or 'master')")
    access_token: str = Field(..., min_length=10, description="Personal access token or deploy token (will be securely encrypted & masked)")


class RepositoryConnectionResponse(BaseModel):
    id: str
    website_id: Optional[str] = None
    provider: str
    repo_name: str
    default_branch: str
    masked_token: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CreateDeploymentTargetRequest(BaseModel):
    website_id: str = Field(..., description="Target website ID")
    name: str = Field(..., min_length=2, max_length=100, description="Target label (e.g., 'Staging Cluster A')")
    environment: str = Field(default="staging", description="'staging' or 'production'")
    target_type: str = Field(default="github_pr", description="'github_pr', 'webhook', or 'staging_cluster'")
    endpoint_url: Optional[str] = None
    is_enabled: bool = Field(default=False, description="Must be explicitly enabled by user")
    health_check_url: Optional[str] = None


class DeploymentTargetResponse(BaseModel):
    id: str
    website_id: str
    name: str
    environment: str
    target_type: str
    endpoint_url: Optional[str] = None
    is_enabled: bool
    health_check_url: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class CreatePullRequestPayload(BaseModel):
    session_id: str = Field(..., description="ID of the approved remediation session from Phase 8")
    repository_id: str = Field(..., description="ID of the connected repository")
    branch_name: Optional[str] = Field(default=None, description="Custom branch name (defaults to patchora/patch-<id>)")
    pr_title: Optional[str] = Field(default=None, description="Custom PR title")
    commit_message: Optional[str] = Field(default=None, description="Custom Git commit message")


class DeployStagingPayload(BaseModel):
    session_id: str = Field(..., description="Approved remediation session ID")
    target_id: Optional[str] = Field(default=None, description="Staging deployment target ID")
    notes: Optional[str] = Field(default=None, max_length=1000)


class DeployProductionPayload(BaseModel):
    session_id: str = Field(..., description="Approved remediation session ID")
    target_id: str = Field(..., description="Production deployment target ID")
    confirmation_token: str = Field(..., description="Strict safety gate: must type 'DEPLOY PRODUCTION'")
    client_notes: Optional[str] = Field(default=None, max_length=1000)


class RollbackPayload(BaseModel):
    reason: str = Field(..., min_length=3, max_length=1000, description="Documented reason for executing rollback")


class DeploymentRecordResponse(BaseModel):
    id: str
    session_id: str
    target_id: Optional[str] = None
    website_id: str
    environment: str
    status: str
    git_branch: str
    git_commit_sha: Optional[str] = None
    pull_request_url: Optional[str] = None
    pull_request_number: Optional[int] = None
    pre_deployment_test_status: str
    client_approved_at: Optional[datetime] = None
    client_notes: Optional[str] = None
    deployed_at: Optional[datetime] = None
    rollback_executed_at: Optional[datetime] = None
    rollback_reason: Optional[str] = None
    audit_trail: Optional[str] = None
    created_at: datetime

    # Contextual display fields
    finding_title: Optional[str] = None
    target_filename: Optional[str] = None
    website_domain: Optional[str] = None

    model_config = {"from_attributes": True}


class CliInstructionsResponse(BaseModel):
    session_id: str
    target_filename: str
    patch_filename: str
    branch_name: str
    cli_commands: List[str]
    git_apply_script: str
    rollback_script: str
    security_notice: str


class AdminDeploymentOverviewResponse(BaseModel):
    total_connected_repositories: int
    total_pull_requests_dispatched: int
    total_staging_deployments: int
    total_production_deployments: int
    production_deployments_enabled: bool
    total_rollbacks_executed: int
