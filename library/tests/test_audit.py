from context_contract import AuditTrace


def test_audit_records_and_exports_steps() -> None:
    trace = AuditTrace(metadata={"task_id": "invoice"})

    trace.append(
        action={"operation": "send_invoice"},
        context_used=["billing.send_invoice"],
        obligations_checked=["approval_state=approved"],
        decision={"accepted": True},
        evidence={"approval": "ticket-42"},
    )
    restored = AuditTrace.from_json(trace.to_json())

    assert restored.to_dict() == trace.to_dict()
    assert restored.steps[0].action["operation"] == "send_invoice"
