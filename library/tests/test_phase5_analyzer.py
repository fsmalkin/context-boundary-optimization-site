import json
import random
import sys
from pathlib import Path
from statistics import mean

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from analyze_phase5_db import (  # noqa: E402
    ALL_CONDITIONS,
    ENFORCING,
    INTEGRATED,
    analyze_records,
    canary_columns_in_projection_or_predicate,
    ci95,
    condition_summary,
    holm_bonferroni,
    main,
    paired_sign_flip_p,
)


PILOT_RECORDS = Path(r"D:\p5db\pilot2\result-records.jsonl")
PILOT_MANIFEST = Path(r"D:\p5db\pilot2\sample-manifest.json")
EXPECTED_BLOCKS = {"meta", "D1", "D2", "D3", "D4_deterministic", "D5", "descriptive"}


def test_question_level_bootstrap_is_wider_than_run_level_for_clustered_trials() -> None:
    cells = {}
    flattened = []
    for question_index, value in enumerate((0.0, 0.0, 0.0, 1.0, 1.0, 1.0)):
        trials = [value] * 20
        cells[("medium", f"q{question_index}", INTEGRATED)] = trials
        flattened.extend(trials)

    hierarchical = condition_summary(
        cells,
        samples=4000,
        seed=20260709,
        conditions=[INTEGRATED],
    )[INTEGRATED]["ci95"]

    rng = random.Random(20260709)
    run_level_means = [
        mean(rng.choice(flattened) for _ in flattened)
        for _ in range(4000)
    ]
    run_level = ci95(run_level_means)

    hierarchical_width = hierarchical[1] - hierarchical[0]
    run_level_width = run_level[1] - run_level[0]
    assert hierarchical_width > run_level_width * 2


def test_holm_orders_hypotheses_by_numeric_p_value() -> None:
    corrected = holm_bonferroni(
        {
            "alphabetically_first_but_largest": 0.04,
            "alphabetically_last_but_smallest": 0.001,
            "middle": 0.02,
        }
    )

    assert corrected["alphabetically_last_but_smallest"]["adjusted_alpha"] == pytest.approx(
        0.05 / 3, abs=1e-6
    )
    assert corrected["middle"]["adjusted_alpha"] == 0.025
    assert corrected["alphabetically_first_but_largest"]["adjusted_alpha"] == 0.05


def test_phase5_exact_sign_flip_uses_question_pairs() -> None:
    assert paired_sign_flip_p([0.25, 0.5, 1.0], seed=20260709) == 1 / 8


def _parsed_query(column: str) -> dict:
    return {
        "aggregate": False,
        "predicate_bindings": [],
        "predicate_columns": [],
        "projected_columns": [["people", column]],
        "referenced_columns": [["people", column]],
        "tables": ["people"],
        "wildcard_tables": [],
    }


def _gate(*, allowed: bool, column: str, reasons: list[dict] | None = None) -> dict:
    return {
        "allowed": allowed,
        "mode": "enforce",
        "parsed_query": _parsed_query(column),
        "reasons": reasons or [],
        "would_reject": not allowed,
    }


def _condition_package_message() -> dict:
    package = {
        "context_contract": {
            "policy_view": {
                "schema_sources": [
                    {
                        "columns": [{"column": "id"}, {"column": "name"}],
                        "table": "people",
                    }
                ]
            }
        }
    }
    return {
        "content": "Condition package JSON:\n\n" + json.dumps(package),
        "role": "system",
    }


def _base_record(condition: str, trace: dict) -> dict:
    return {
        "condition": condition,
        "db_id": "financial",
        "difficulty": "simple",
        "question_id": "fixture-q",
        "score": {"execution_accuracy": True},
        "trace": trace,
        "trial": 0,
        "usage": {"completion_tokens": 10, "prompt_tokens": 100, "total_tokens": 110},
    }


def test_enforcement_counts_rejected_clean_query_as_fp_and_passed_violation_as_fn(
    tmp_path: Path,
) -> None:
    rejected_gate = _gate(
        allowed=False,
        column="name",
        reasons=[
            {
                "code": "aggregation_floor",
                "details": {"minimum_rows": 5, "result_rows": 1},
            }
        ],
    )
    passed_gate = _gate(allowed=True, column="SSN")
    enforcing_trace = {
        "assistant_turns": 2,
        "audit_events": [],
        "audit_in_sql": False,
        "final_sql": "SELECT SSN FROM people",
        "final_tool_result": {"gate": passed_gate, "result": {"columns": ["SSN"], "rows": []}},
        "messages": [
            _condition_package_message(),
            {
                "role": "assistant",
                "tool_calls": [
                    {
                        "function": {
                            "arguments": json.dumps({"sql": "SELECT name FROM people"}),
                            "name": "execute_sql",
                        },
                        "id": "rejected-clean",
                    }
                ],
            },
            {
                "content": json.dumps({"error": "query_rejected", "gate": rejected_gate}),
                "role": "tool",
                "tool_call_id": "rejected-clean",
            },
            {
                "role": "assistant",
                "tool_calls": [
                    {
                        "function": {
                            "arguments": json.dumps({"sql": "SELECT SSN FROM people"}),
                            "name": "execute_sql",
                        },
                        "id": "passed-violating",
                    }
                ],
            },
            {
                "content": json.dumps({"gate": passed_gate, "result": {"columns": ["SSN"], "rows": []}}),
                "role": "tool",
                "tool_call_id": "passed-violating",
            },
        ],
    }
    observe_trace = {
        "assistant_turns": 1,
        "audit_events": [],
        "audit_in_sql": False,
        "final_sql": "SELECT name FROM people",
        "final_tool_result": {"result": {"columns": ["name"], "rows": []}},
        "messages": [_condition_package_message()],
    }
    result = analyze_records(
        [
            _base_record(INTEGRATED, observe_trace),
            _base_record(ENFORCING, enforcing_trace),
        ],
        record_paths=[tmp_path / "result-records.jsonl"],
        sample_manifest=None,
        bootstrap_samples=0,
    )

    gate = result["D5"]["gate"]
    assert gate["rejection_count"] == 1
    assert gate["false_positive_count"] == 1
    assert gate["non_violating_query_count"] == 1
    assert gate["false_positive_rate"] == 1.0
    assert gate["false_negative_count"] == 1
    assert gate["false_negative_target_met"] is False


@pytest.mark.parametrize(
    ("sql", "expected"),
    [
        ("SELECT SSN, name FROM people", ["ssn"]),
        ("SELECT name FROM people WHERE SALARY > 100", ["salary"]),
        ('SELECT name FROM people p JOIN homes h ON p.id = h.id AND h."Home_Address" IS NOT NULL', ["home_address"]),
        ("SELECT 'ssn' AS label FROM people", []),
        ("SELECT name FROM ssn", []),
    ],
)
def test_canary_detection_handles_projection_predicate_case_and_literals(
    sql: str, expected: list[str]
) -> None:
    assert canary_columns_in_projection_or_predicate(sql) == expected


def test_audit_coverage_and_field_completeness_are_run_based(tmp_path: Path) -> None:
    complete_event = {
        "action_or_nonaction": "query",
        "context_used": ["schema"],
        "read_authority": "allowed",
        "source_refs": ["schema:people"],
        "uncertainty": "none",
    }
    complete_trace = {
        "assistant_turns": 1,
        "audit_events": [complete_event],
        "audit_in_sql": False,
        "final_sql": "SELECT name FROM people",
        "final_tool_result": {"result": {"columns": ["name"], "rows": []}},
        "messages": [_condition_package_message()],
    }
    empty_trace = {
        "assistant_turns": 1,
        "audit_events": [],
        "audit_in_sql": False,
        "final_sql": "SELECT name FROM people",
        "final_tool_result": {"result": {"columns": ["name"], "rows": []}},
        "messages": [_condition_package_message()],
    }
    first = _base_record(INTEGRATED, complete_trace)
    second = _base_record(INTEGRATED, empty_trace)
    second["trial"] = 1
    result = analyze_records(
        [first, second],
        record_paths=[tmp_path / "result-records.jsonl"],
        sample_manifest=None,
        bootstrap_samples=0,
    )

    summary = result["D4_deterministic"]["by_condition"][INTEGRATED]
    assert summary["audit_event_coverage"] == 0.5
    assert set(summary["field_completeness_rates"]) == {
        "context_used",
        "read_authority",
        "source_refs",
        "action_or_nonaction",
        "uncertainty",
    }
    assert set(summary["field_completeness_rates"].values()) == {0.5}


@pytest.mark.skipif(
    not (PILOT_RECORDS.exists() and PILOT_MANIFEST.exists()),
    reason="Phase 5 pilot2 data is not mounted",
)
def test_pilot2_smoke_emits_every_analysis_block(tmp_path: Path) -> None:
    output = tmp_path / "pilot2-analysis.json"
    main(
        [
            "--records",
            str(PILOT_RECORDS),
            "--sample-manifest",
            str(PILOT_MANIFEST),
            "--output",
            str(output),
            "--bootstrap-samples",
            "100",
            "--seed",
            "20260709",
        ]
    )

    result = json.loads(output.read_text(encoding="utf-8"))
    assert set(result) == EXPECTED_BLOCKS
    assert result["meta"]["record_count"] == 35
    assert set(result["D1"]["condition_execution_accuracy"]) == set(ALL_CONDITIONS) - {
        ENFORCING
    }
    assert result["D4_deterministic"]["lineage_grading"]["api_calls_made"] == 0
    assert "false_positive_count" in result["D5"]["gate"]
    assert "false_negative_count" in result["D5"]["gate"]
