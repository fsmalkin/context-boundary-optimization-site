from context_contract import ContextContract, Gate, ObligationSpec


def test_gate_accepts_compliant_action() -> None:
    contract = ContextContract(
        authority=ObligationSpec(
            preconditions={"send_invoice": ["approval_state=approved", "argument:customer_id"]}
        )
    )
    gate = Gate(contract)

    decision = gate.check(
        {
            "operation": "send_invoice",
            "arguments": {"customer_id": "cus_123"},
            "approval_state": "approved",
        }
    )

    assert decision.accepted is True
    assert decision.missing == []


def test_gate_rejects_precondition_violation() -> None:
    contract = ContextContract(
        authority=ObligationSpec(
            preconditions={"send_invoice": ["approval_state=approved", "argument:customer_id"]}
        )
    )
    gate = Gate(contract)

    decision = gate.check(
        {
            "operation": "send_invoice",
            "arguments": {},
            "approval_state": "missing",
        }
    )

    assert decision.accepted is False
    assert decision.reason == "missing_preconditions"
    assert decision.missing == ["approval_state=approved", "argument:customer_id"]
