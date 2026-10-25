import { apiClient } from './client'
import {
  AdminDeploymentOverview,
  CliInstructions,
  CreateDeploymentTargetRequest,
  CreatePullRequestPayload,
  CreateRepositoryConnectionRequest,
  DeployProductionPayload,
  DeployStagingPayload,
  DeploymentRecord,
  DeploymentTarget,
  RepositoryConnection,
  RollbackPayload,
} from '@/types/deployment'

export async function connectRepository(payload: CreateRepositoryConnectionRequest): Promise<RepositoryConnection> {
  const res = await apiClient.post<RepositoryConnection>('/api/deployment/repositories', payload)
  return res.data
}

export async function listRepositories(): Promise<RepositoryConnection[]> {
  const res = await apiClient.get<RepositoryConnection[]>('/api/deployment/repositories')
  return res.data
}

export async function disconnectRepository(repoId: string): Promise<void> {
  await apiClient.delete(`/api/deployment/repositories/${repoId}`)
}

export async function createDeploymentTarget(payload: CreateDeploymentTargetRequest): Promise<DeploymentTarget> {
  const res = await apiClient.post<DeploymentTarget>('/api/deployment/targets', payload)
  return res.data
}

export async function listDeploymentTargets(websiteId?: string): Promise<DeploymentTarget[]> {
  const res = await apiClient.get<DeploymentTarget[]>('/api/deployment/targets', {
    params: { website_id: websiteId },
  })
  return res.data
}

export async function createPullRequest(payload: CreatePullRequestPayload): Promise<DeploymentRecord> {
  const res = await apiClient.post<DeploymentRecord>('/api/deployment/create-pr', payload)
  return res.data
}

export async function deployToStaging(payload: DeployStagingPayload): Promise<DeploymentRecord> {
  const res = await apiClient.post<DeploymentRecord>('/api/deployment/deploy-staging', payload)
  return res.data
}

export async function deployToProduction(payload: DeployProductionPayload): Promise<DeploymentRecord> {
  const res = await apiClient.post<DeploymentRecord>('/api/deployment/deploy-production', payload)
  return res.data
}

export async function rollbackDeployment(deploymentId: string, payload: RollbackPayload): Promise<DeploymentRecord> {
  const res = await apiClient.post<DeploymentRecord>(`/api/deployment/${deploymentId}/rollback`, payload)
  return res.data
}

export async function getCliInstructions(sessionId: string): Promise<CliInstructions> {
  const res = await apiClient.get<CliInstructions>(`/api/deployment/cli-instructions/${sessionId}`)
  return res.data
}

export async function getDeploymentHistory(): Promise<DeploymentRecord[]> {
  const res = await apiClient.get<DeploymentRecord[]>('/api/deployment/history')
  return res.data
}

export async function adminGetDeploymentOverview(): Promise<AdminDeploymentOverview> {
  const res = await apiClient.get<AdminDeploymentOverview>('/api/deployment/admin/overview')
  return res.data
}
