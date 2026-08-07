from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from context_contract import ContextContract, ObligationSpec


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "context_contract", *args],
        check=True,
        text=True,
        capture_output=True,
    )


def write_contract(path: Path) -> None:
    contract = ContextContract(
        name="billing-service",
        authority=ObligationSpec(
            preconditions={"send_invoice": ["approval_state=approved", "argument:customer_id"]}
        ),
    )
    path.write_text(contract.to_json(), encoding="utf-8")


def test_cli_scaffold_stdout_and_out_path(tmp_path: Path) -> None:
    contract_path = tmp_path / "contract.json"
    out_path = tmp_path / "scaffold.py"
    write_contract(contract_path)

    stdout = run_cli("scaffold", str(contract_path)).stdout
    run_cli("scaffold", str(contract_path), "--out", str(out_path))

    assert "focused_view(catalog, task, contract, k=5)" in stdout
    assert "Gate(contract)" in stdout
    assert "score_trace(trace, contract)" in stdout
    assert out_path.read_text(encoding="utf-8") == stdout


def test_cli_advise_emits_heuristic_contract(tmp_path: Path) -> None:
    service_path = tmp_path / "service.json"
    service_path.write_text(
        json.dumps(
            {
                "name": "billing-service",
                "use_case": "Send customer invoice emails from approved drafts.",
                "operations": [
                    {"name": "send_invoice", "description": "Externally-visible email send that requires approval."},
                    {"name": "lookup_invoice", "description": "Read current invoice draft source."},
                ],
            }
        ),
        encoding="utf-8",
    )

    payload = json.loads(run_cli("advise", str(service_path)).stdout)

    assert payload["notice"].startswith("Heuristic starting point")
    assert payload["axis_review"]["authority"]["status"] == "likely_applies"
    assert payload["axis_review"]["provenance"]["status"] == "likely_applies"
    assert payload["contract"]["authority"]["preconditions"]["send_invoice"] == ["approval_state=approved"]


def test_cli_check_prints_gate_decision(tmp_path: Path) -> None:
    contract_path = tmp_path / "contract.json"
    action_path = tmp_path / "action.json"
    write_contract(contract_path)
    action_path.write_text(
        json.dumps({"operation": "send_invoice", "arguments": {}, "approval_state": "missing"}),
        encoding="utf-8",
    )

    decision = json.loads(run_cli("check", str(contract_path), str(action_path)).stdout)

    assert decision["accepted"] is False
    assert decision["missing"] == ["approval_state=approved", "argument:customer_id"]
