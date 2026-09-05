export type Role =
  | "super_admin"
  | "compliance_analyst"
  | "product_manager"
  | "support_lead";

export type Permission =
  | "kyc:read"
  | "kyc:write"
  | "feature_flags:read"
  | "feature_flags:write"
  | "refunds:read"
  | "refunds:write"
  | "users:read"
  | "users:write";

export interface User {
  id: string;
  name: string;
  email: string;
  job_title: string;
  department: string;
  location: string;
  last_active: string;
  access_review: string;
  mfa_status: string;
  roles: Role[];
  permissions: Permission[];
  avatar_color: string;
}

export interface KycCase {
  id: string;
  customer: string;
  customer_id: string;
  country: string;
  entity_type: "Individual" | "Business";
  risk: "High" | "Medium" | "Low";
  reason: string;
  signals: string[];
  submitted: string;
  sla: string;
  sla_state: "On track" | "Due soon" | "Breached";
  status: string;
  assignee_id: string | null;
  assignee: string;
  audit: AuditEvent[];
}

export interface AuditEvent {
  action: string;
  actor: string;
  at: string;
}

export interface FeatureFlag {
  id: string;
  name: string;
  description: string;
  enabled: boolean;
  environment: string;
  rollout: string;
  owner: string;
  owner_contact: string;
  flag_type: "Release" | "Experiment" | "Kill switch";
  risk: "Standard" | "Elevated" | "Critical";
  expires: string;
  last_changed: string;
  change_ticket: string;
  audit: AuditEvent[];
}

export interface Refund {
  id: string;
  customer: string;
  customer_id: string;
  amount: string;
  reason: string;
  channel: string;
  payment_method: string;
  age: string;
  sla: string;
  sla_state: "On track" | "Due soon" | "Breached";
  status: string;
  assignee_id: string | null;
  assignee: string;
  risk_flags: string[];
  required_approvals: number;
  approval_count: number;
  approved_by: string[];
  audit: AuditEvent[];
}

export interface RefundResponse {
  summary: {
    pending_count: number;
    pending_value: string;
    processed_today: number;
    approval_rate: string;
  };
  items: Refund[];
}
