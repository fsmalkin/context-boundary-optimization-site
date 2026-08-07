from pathlib import Path
import importlib.util


def load_scaffold():
    path = Path(__file__).with_name("scaffold.py")
    spec = importlib.util.spec_from_file_location("billing_scaffold", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_billing_service_scaffold_accepts_and_rejects() -> None:
    scaffold = load_scaffold()
    catalog = [
        {"name": "send_invoice", "description": "Send approved invoice to customer", "importance": 1},
        {"name": "delete_customer", "description": "Delete customer account"},
    ]
    task = {"title": "send invoice", "required_tools": ["send_invoice"]}
    compliant = {
        "operation": "send_invoice",
        "arguments": {"customer_id": "cus_123", "invoice_id": "inv_456"},
        "approval_state": "approved",
        "source_ids": ["approval-ticket-42"],
    }
    violation = {
        "operation": "send_invoice",
        "arguments": {"customer_id": "cus_123"},
        "approval_state": "missing",
        "source_ids": [],
    }

    accepted = scaffold.handle_task(catalog, task, compliant)
    rejected = scaffold.handle_task(catalog, task, violation)

    assert accepted["decision"]["accepted"] is True
    assert accepted["score"]["auditability_score"] == 5
    assert rejected["decision"]["accepted"] is False
    assert rejected["score"]["authority_boundary_violations"] == 1
