import type {
  FeatureFlag,
  KycCase,
  Refund,
  RefundResponse,
  Role,
  User,
} from "./types";

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

async function request<T>(
  path: string,
  userId: string,
  options?: RequestInit,
): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      "X-Demo-User": userId,
      ...options?.headers,
    },
  });

  if (!response.ok) {
    const error = (await response.json()) as { detail?: string };
    throw new Error(error.detail ?? "The request could not be completed.");
  }

  return (await response.json()) as T;
}

export const api = {
  currentUser: (userId: string) =>
    request<User>("/api/auth/me", userId),
  kycCases: (userId: string) =>
    request<KycCase[]>("/api/kyc/cases", userId),
  assignKycCase: (userId: string, caseId: string) =>
    request<KycCase>(`/api/kyc/cases/${caseId}/assign`, userId, {
      method: "POST",
      body: JSON.stringify({ reason: "Claimed from the manual review queue" }),
    }),
  featureFlags: (userId: string) =>
    request<FeatureFlag[]>("/api/feature-flags", userId),
  updateFeatureFlag: (userId: string, flagId: string, enabled: boolean, reason: string) =>
    request<FeatureFlag>(`/api/feature-flags/${flagId}`, userId, {
      method: "PUT",
      body: JSON.stringify({ enabled, reason }),
    }),
  refunds: (userId: string) =>
    request<RefundResponse>("/api/refunds", userId),
  assignRefund: (userId: string, refundId: string) =>
    request<Refund>(`/api/refunds/${refundId}/assign`, userId, {
      method: "POST",
      body: JSON.stringify({ reason: "Claimed from the refund operations queue" }),
    }),
  approveRefund: (userId: string, refundId: string) =>
    request<Refund>(`/api/refunds/${refundId}/approve`, userId, {
      method: "POST",
      body: JSON.stringify({ reason: "Reviewed in operations console" }),
    }),
  users: (userId: string) =>
    request<User[]>("/api/admin/users", userId),
  updateRoles: (
    userId: string,
    targetUserId: string,
    roles: Role[],
    reason: string,
  ) =>
    request<User>(`/api/admin/users/${targetUserId}/roles`, userId, {
      method: "PUT",
      body: JSON.stringify({ roles, reason }),
    }),
};
