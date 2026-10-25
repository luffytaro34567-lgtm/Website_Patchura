export type VerificationMethod = 'file' | 'meta_tag' | 'dns_txt'
export type VerificationStatus = 'pending' | 'verified' | 'failed'

export interface ScanAuthorization {
  id: string
  website_id: string
  is_authorized: boolean
  authorized_by_name: string
  authorized_by_email: string
  legal_confirmation: boolean
  allowed_scan_types: string
  authorized_at: string | null
  expires_at: string | null
  is_revoked: boolean
  revoked_at: string | null
  revocation_reason: string | null
}

export interface VerificationInstructions {
  method: string
  token: string
  file_path?: string
  file_content?: string
  meta_tag_snippet?: string
  dns_record_name?: string
  dns_txt_value?: string
}

export interface Website {
  id: string
  user_id: string
  name: string
  target_url: string
  domain: string
  verification_method: VerificationMethod
  verification_token: string
  verification_status: VerificationStatus
  verified_at: string | null
  last_verification_attempt: string | null
  verification_error: string | null
  is_suspended_by_admin: boolean
  suspension_reason: string | null
  created_at: string
  authorization: ScanAuthorization | null
  instructions?: VerificationInstructions
}

export interface CreateWebsiteData {
  name: string
  target_url: string
  verification_method: VerificationMethod
}

export interface ScanAuthorizationData {
  authorized_by_name: string
  authorized_by_email: string
  legal_confirmation: boolean
  allowed_scan_types: string
}

export interface VerificationResult {
  is_verified: boolean
  verification_status: VerificationStatus
  message: string
  verified_at: string | null
}
