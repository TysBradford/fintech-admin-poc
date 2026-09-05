class DemoKycDataSource:
    def list_cases(self) -> list[dict[str, object]]:
        return [
            {
                "id": "KYC-1048",
                "customer": "Nadia Okafor",
                "country": "GB",
                "risk": "High",
                "reason": "Document mismatch",
                "submitted": "12 min ago",
                "status": "Needs review",
            },
            {
                "id": "KYC-1047",
                "customer": "Mateo Silva",
                "country": "PT",
                "risk": "Medium",
                "reason": "Source of funds",
                "submitted": "34 min ago",
                "status": "In review",
            },
            {
                "id": "KYC-1045",
                "customer": "Elena Rossi",
                "country": "IT",
                "risk": "Low",
                "reason": "Address verification",
                "submitted": "1 hr ago",
                "status": "Needs review",
            },
            {
                "id": "KYC-1042",
                "customer": "Tariq Rahman",
                "country": "AE",
                "risk": "Medium",
                "reason": "Identity verification",
                "submitted": "2 hrs ago",
                "status": "Escalated",
            },
        ]


class DemoFeatureFlagProvider:
    def __init__(self) -> None:
        self.flags = [
            {
                "id": "instant-bank-verification",
                "name": "Instant bank verification",
                "description": "Use the new verification provider during account linking.",
                "enabled": True,
                "environment": "Production",
                "rollout": "100%",
                "owner": "Identity",
            },
            {
                "id": "refund-self-service",
                "name": "Refund self-service",
                "description": "Let eligible customers request refunds from the app.",
                "enabled": False,
                "environment": "Production",
                "rollout": "0%",
                "owner": "Payments",
            },
            {
                "id": "kyc-risk-signals-v2",
                "name": "KYC risk signals v2",
                "description": "Enable the second-generation risk scoring pipeline.",
                "enabled": True,
                "environment": "Staging",
                "rollout": "25%",
                "owner": "Compliance",
            },
        ]

    def list_flags(self) -> list[dict[str, object]]:
        return self.flags

    def set_flag(self, flag_id: str, enabled: bool) -> dict[str, object]:
        for flag in self.flags:
            if flag["id"] == flag_id:
                flag["enabled"] = enabled
                return flag
        raise KeyError(flag_id)


class DemoPaymentsProvider:
    def __init__(self) -> None:
        self.refunds = [
            {
                "id": "RF-8291",
                "customer": "Sophie Williams",
                "amount": "£1,249.00",
                "amount_minor": 124900,
                "reason": "Duplicate charge",
                "age": "18 min",
                "status": "Awaiting approval",
                "required_approvals": 2,
                "approval_count": 0,
                "approved_by": [],
            },
            {
                "id": "RF-8288",
                "customer": "Daniel Green",
                "amount": "£89.50",
                "amount_minor": 8950,
                "reason": "Service not received",
                "age": "42 min",
                "status": "Under review",
                "required_approvals": 1,
                "approval_count": 0,
                "approved_by": [],
            },
            {
                "id": "RF-8283",
                "customer": "Chloe Adams",
                "amount": "£425.20",
                "amount_minor": 42520,
                "reason": "Merchant dispute",
                "age": "1 hr",
                "status": "Awaiting approval",
                "required_approvals": 1,
                "approval_count": 0,
                "approved_by": [],
            },
        ]

    def refund_summary(self) -> dict[str, object]:
        pending = [refund for refund in self.refunds if refund["status"] != "Approved"]
        pending_value = 0
        for refund in pending:
            amount_minor = refund["amount_minor"]
            if not isinstance(amount_minor, int):
                raise TypeError("Refund amount data is invalid")
            pending_value += amount_minor
        return {
            "pending_count": len(pending),
            "pending_value": f"£{pending_value / 100:,.2f}",
            "processed_today": 23 + len(self.refunds) - len(pending),
            "approval_rate": "91.4%",
        }

    def list_refunds(self) -> list[dict[str, object]]:
        return self.refunds

    def approve_refund(
        self,
        refund_id: str,
        approver_id: str,
        reason: str,
    ) -> dict[str, object]:
        for refund in self.refunds:
            if refund["id"] != refund_id:
                continue

            approved_by = refund["approved_by"]
            if not isinstance(approved_by, list):
                raise TypeError("Refund approval data is invalid")
            if approver_id in approved_by:
                raise PermissionError("A distinct approver is required")

            required_approvals = refund["required_approvals"]
            if not isinstance(required_approvals, int):
                raise TypeError("Refund approval policy is invalid")
            approved_by.append(approver_id)
            refund["approval_count"] = len(approved_by)
            refund["last_approval_reason"] = reason
            if len(approved_by) >= required_approvals:
                refund["status"] = "Approved"
            else:
                refund["status"] = "Awaiting second approval"
            return refund

        raise KeyError(refund_id)
