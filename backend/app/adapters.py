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
    def refund_summary(self) -> dict[str, object]:
        return {
            "pending_count": 8,
            "pending_value": "£4,860.42",
            "processed_today": 23,
            "approval_rate": "91.4%",
        }

    def list_refunds(self) -> list[dict[str, object]]:
        return [
            {
                "id": "RF-8291",
                "customer": "Sophie Williams",
                "amount": "£1,249.00",
                "reason": "Duplicate charge",
                "age": "18 min",
                "status": "Awaiting approval",
            },
            {
                "id": "RF-8288",
                "customer": "Daniel Green",
                "amount": "£89.50",
                "reason": "Service not received",
                "age": "42 min",
                "status": "Under review",
            },
            {
                "id": "RF-8283",
                "customer": "Chloe Adams",
                "amount": "£425.20",
                "reason": "Merchant dispute",
                "age": "1 hr",
                "status": "Awaiting approval",
            },
        ]
