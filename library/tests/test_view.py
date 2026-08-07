from context_contract import ContextContract, focused_view


def test_focused_view_selects_relevant_tools_and_drops_distractors() -> None:
    catalog = [
        {"name": "billing.send_invoice", "description": "Send invoice email", "importance": 1},
        {"name": "crm.delete_account", "description": "Delete account"},
        {"name": "docs.search", "description": "Search documentation"},
    ]
    task = {
        "title": "send approved invoice",
        "required_tools": ["billing.send_invoice"],
    }

    view = focused_view(catalog, task, ContextContract(), k=1)

    assert [item["name"] for item in view] == ["billing.send_invoice"]
    assert "crm.delete_account" not in [item["name"] for item in view]
    assert "_doi_score" in view[0]
