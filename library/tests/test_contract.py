from context_contract import ContextContract, ObligationSpec


def test_contract_json_round_trip() -> None:
    contract = ContextContract(
        name="calendar",
        version="2026-07",
        required_context=ObligationSpec(requires=["calendar_id"]),
        authority=ObligationSpec(
            requires=["approval"],
            preconditions={"create_event": ["approval_state=approved"]},
        ),
        output_audit=ObligationSpec(promises=["compact trace"]),
    )

    restored = ContextContract.from_json(contract.to_json())

    assert restored.to_dict() == contract.to_dict()
    assert restored.authority.preconditions["create_event"] == ["approval_state=approved"]
