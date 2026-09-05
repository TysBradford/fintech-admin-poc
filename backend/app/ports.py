from typing import Protocol


class KycDataSource(Protocol):
    def list_cases(self) -> list[dict[str, object]]: ...


class FeatureFlagProvider(Protocol):
    def list_flags(self) -> list[dict[str, object]]: ...

    def set_flag(self, flag_id: str, enabled: bool) -> dict[str, object]: ...


class PaymentsProvider(Protocol):
    def refund_summary(self) -> dict[str, object]: ...

    def list_refunds(self) -> list[dict[str, object]]: ...

    def approve_refund(
        self,
        refund_id: str,
        approver_id: str,
        reason: str,
    ) -> dict[str, object]: ...
