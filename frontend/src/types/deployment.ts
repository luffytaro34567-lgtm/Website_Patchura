export type DeploymentEnvironment = 'staging' | 'production' | 'git_pr_only'

export type DeploymentStatus =
  | 'pending'
  | 'pr_created'
  | 'staged'
  | 'verifying'
  | 'deployed'
  | 'failed'
  | 'rolled_back'

export interface RepositoryConnection {
  id: string
  website_id?: string | null
  provider: string
  repo_name: string
  default_branch: string
  masked_token: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface DeploymentTarget {
  id: string
  website_id: string
  name: string
  environment: DeploymentEnvironment
  target_type: string
  endpoint_url?: string | null
  is_enabled: boolean
  health_check_url?: string | null
  created_at: string
}

export interface DeploymentRecord {
  id: string
  session_id: string
  target_id?: string | null
  website_id: string
  environment: DeploymentEnvironment
  status: DeploymentStatus
  git_branch: string
  git_commit_sha?: string | null
  pull_request_url?: string | null
  pull_request_number?: number | null
  pre_deployment_test_status: string
  client_approved_at?: string | null
  client_notes?: string | null
  deployed_at?: string | null
  rollback_executed_at?: string | null
  rollback_reason?: string | null
  audit_trail?: string | null
  created_at: string

  // Contextual labels
  finding_title?: string
  target_filename?: string
  website_domain?: string
}

export interface CreateRepositoryConnectionRequest {
  website_id?: string
  provider?: string
  repo_name: string
  default_branch?: string
  access_token: string
}

export interface CreateDeploymentTargetRequest {
  website_id: string
  name: string
  environment: string
  target_type?: string
  endpoint_url?: string
  is_enabled?: boolean
  health_check_url?: string
}

export interface CreatePullRequestPayload {
  session_id: string
  repository_id: string
  branch_name?: string
  pr_title?: string
  commit_message?: string
}

export interface DeployStagingPayload {
  session_id: string
  target_id?: string
  notes?: string
}

export interface DeployProductionPayload {
  session_id: string
  target_id: string
  confirmation_token: string
  client_notes?: string
}

export interface RollbackPayload {
  reason: string
}

export interface CliInstructions {
  session_id: string
  target_filename: string
  patch_filename: string
  branch_name: string
  cli_commands: string[]
  git_apply_script: string
  rollback_script: string
  security_notice: string
}

export interface AdminDeploymentOverview {
  total_connected_repositories: number
  total_pull_requests_dispatched: number
  total_staging_deployments: number
  total_production_deployments: number
  production_deployments_enabled: boolean
  total_rollbacks_executed: number
}
