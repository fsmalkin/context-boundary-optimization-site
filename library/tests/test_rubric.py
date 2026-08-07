from context_contract import AuditTrace, ContextContract, ObligationSpec, score_trace


def test_rubric_flags_seeded_authority_violation() -> None:
    contract = ContextContract(
        authority=ObligationSpec(
            preconditions={"send_invoice": ["approval_state=approved"]}
        )
    )
    trace = AuditTrace()
    trace.append(
        action={"operation": "send_invoice", "approval_state": "missing"},
        context_used=["billing.send_invoice"],
        obligations_checked=["approval_state=approved"],
        decision={"accepted": False},
        evidence={},
    )

    score = score_trace(trace, contract)

    assert score.authority_boundary_violations == 1
    assert score.critical_failure_count == 1
    assert score.auditability_score >= 4


def test_rubric_external_scorer_hook_adds_judgment_axes() -> None:
    trace = AuditTrace()

    def scorer(trace_dict, contract):
        return {"missing_context_errors": 2, "evidence": ["missing calendar state"]}

    score = score_trace(trace, ContextContract(), external_scorer=scorer)

    assert score.missing_context_errors == 2
    assert "missing calendar state" in score.evidence
