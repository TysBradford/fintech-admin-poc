export type Role =
  | "super_admin"
  | "compliance_analyst"
  | "product_manager"
  | "support_lead";

export type Permission =
  | "kyc:read"
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
  roles: Role[];
  permissions: Permission[];
  avatar_color: string;
}

export interface KycCase {
  id: string;
  customer: string;
  country: string;
  risk: "High" | "Medium" | "Low";
  reason: string;
  submitted: string;
  status: string;
}

export interface FeatureFlag {
  id: string;
  name: string;
  description: string;
  enabled: boolean;
  environment: string;
  rollout: string;
  owner: string;
}

export interface Refund {
  id: string;
  customer: string;
  amount: string;
  reason: string;
  age: string;
  status: string;
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
