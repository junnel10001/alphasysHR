// Invitation types based on backend schemas

export enum InvitationStatus {
  PENDING = 'pending',
  ACCEPTED = 'accepted',
  EXPIRED = 'expired',
  REVOKED = 'revoked'
}

export interface InvitationBase {
  email: string;
  role_id: number;
  department_id?: number;
  employee_profile_id?: number;
}

export interface InvitationCreate extends InvitationBase {
  expires_days?: number;
}

export interface InvitationAccept {
  token: string;
  username: string;
  password: string;
  first_name: string;
  last_name: string;
  phone_number?: string;
}

export interface InvitationUpdate {
  status?: InvitationStatus;
  expires_at?: string;
  revoked_at?: string;
}

export interface InvitedByUser {
  user_id: number;
  username: string;
  first_name: string;
  last_name: string;
}

export interface Role {
  role_id: number;
  role_name: string;
  description?: string;
}

export interface Department {
  department_id: number;
  department_name: string;
  description?: string;
}

export interface EmployeeProfile {
  employee_id: number;
  first_name: string;
  last_name: string;
  email?: string;
}

export interface Invitation {
  invitation_id: number;
  email: string;
  token: string;
  invited_by: number;
  role_id: number;
  department_id?: number;
  employee_profile_id?: number;
  status: InvitationStatus;
  expires_at: string;
  accepted_at?: string;
  revoked_at?: string;
  created_at: string;
  updated_at: string;
  
  // Optional nested objects
  invited_by_user?: InvitedByUser;
  role?: Role;
  department?: Department;
  employee_profile?: EmployeeProfile;
}

export interface InvitationList {
  invitations: Invitation[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

export interface InvitationResend {
  invitation_id: number;
  expires_days?: number;
}

export interface InvitationRevoke {
  invitation_id: number;
  reason?: string;
}

export interface InvitationTokenValidate {
  token: string;
  is_valid: boolean;
  invitation_data?: any;
  error_message?: string;
}

export interface InvitationAcceptResponse {
  success: boolean;
  message: string;
  user_id?: number;
  access_token?: string;
}

export interface UserCreationFromInvitation {
  username: string;
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  phone_number?: string;
  role_id: number;
  department_id?: number;
  hourly_rate: number;
  date_hired: string;
}

export interface InvitationStatistics {
  total_invitations: number;
  pending_invitations: number;
  accepted_invitations: number;
  expired_invitations: number;
  revoked_invitations: number;
  invitations_this_month: number;
  acceptance_rate: number;
}

export interface InvitationEmailContent {
  to_email: string;
  subject: string;
  body: string;
  invitation_link: string;
  expires_at: string;
  invited_by_name: string;
  role_name: string;
  department_name?: string;
}

// Form validation types
export interface InvitationFormData {
  email: string;
  role_id: number;
  department_id?: number;
  employee_profile_id?: number;
  expires_days?: number;
}

export interface InvitationAcceptFormData {
  token: string;
  username: string;
  password: string;
  confirm_password: string;
  first_name: string;
  last_name: string;
  phone_number?: string;
}

// API request/response types
export interface InvitationsQueryParams {
  skip?: number;
  limit?: number;
  status_filter?: string;
  invited_by_filter?: number;
}

export interface InvitationsResponse {
  invitations: Invitation[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

// Component props types
export interface InvitationDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess?: (invitation: Invitation) => void;
  employeeId?: number;
  defaultEmail?: string;
}

export interface InvitationStatusBadgeProps {
  status: InvitationStatus;
  className?: string;
}

export interface InvitationActionsProps {
  invitation: Invitation;
  onResend?: (invitationId: number) => void;
  onRevoke?: (invitationId: number, reason?: string) => void;
  onView?: (invitationId: number) => void;
  className?: string;
}

export interface InvitationListProps {
  invitations: Invitation[];
  loading?: boolean;
  onRefresh?: () => void;
  onInvitationAction?: (action: string, invitation: Invitation) => void;
  className?: string;
}

export interface InvitationManagementPageProps {
  // Add any specific props for the main page
}

export interface InvitationAcceptPageProps {
  token: string;
}

// Utility types
export type InvitationStatusColor = 'default' | 'secondary' | 'destructive' | 'outline' | 'success' | 'warning';

export interface InvitationStatusConfig {
  label: string;
  color: InvitationStatusColor;
  icon?: any; // Lucide icon component
}