import json
import sys
import types
from argparse import Namespace
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from analyze_tau2_phase1 import analyze
from tau2_condition_builder import (
    CANONICAL_CONDITIONS,
    DEFAULT_TAU2_ROOT,
    build_condition_set,
    stable_json,
)
from tau2_grade import (
    assert_not_gpt5_family,
    gemini_request,
    request_body,
    xai_request,
)
from tau2_trace_normalize import leakage_findings, normalize_inputs
from run_tau2_phase1 import (
    DEFAULT_PHASE1_SEED,
    NATIVE_AGENT_NAME,
    NATIVE_BASELINE_CONDITION,
    build_native_prompt_surface,
    native_result_records,
    resolve_slice,
    sample_tasks,
)


def write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="ascii")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="ascii")


def fake_tau2_root(tmp_path: Path) -> Path:
    root = tmp_path / "tau2"
    domain_root = root / "data" / "tau2" / "domains" / "airline"
    write_text(
        domain_root / "policy.md",
        "\n".join(
            [
                "# Airline Agent Policy",
                "",
                "## Domain Basic",
                "Users have profiles and reservations.",
                "",
                "## Book flight",
                "Book only after collecting passenger and payment details.",
                "",
                "## Modify flight",
                "Modify only eligible reservations.",
                "",
                "## Cancel flight",
                "Cancel only when policy permits and after confirmation.",
                "",
                "## Refunds and Compensation",
                "Compensation requires confirmed eligibility.",
                "",
            ]
        ),
    )
    write_json(
        domain_root / "tasks.json",
        [
            {
                "id": "A1",
                "user_scenario": {
                    "instructions": {
                        "domain": "airline",
                        "reason_for_call": "Cancel reservation ABC123.",
                        "task_instructions": "Ask for help cancelling.",
                        "known_info": "User id user_1.",
                    }
                },
                "initial_state": None,
                "evaluation_criteria": {
                    "actions": [{"name": "SHOULD_NOT_LEAK"}],
                    "reward_basis": ["SHOULD_NOT_LEAK"],
                },
            }
        ],
    )
    return root


def install_fake_tau2_build(monkeypatch: pytest.MonkeyPatch, policy: str) -> None:
    class FakeTool:
        name = "lookup_reservation"

        @property
        def openai_schema(self):
            return {
                "type": "function",
                "function": {
                    "name": self.name,
                    "description": "Read reservation details.",
                    "parameters": {"type": "object", "properties": {}},
                },
            }

    class FakeEnvironment:
        def get_policy(self):
            return policy

        def get_tools(self):
            return [FakeTool()]

    class FakeAgent:
        def __init__(self, domain_policy: str, tools):
            self.domain_policy = domain_policy
            self.tools = tools
            self.system_prompt = (
                "<instructions>Use the standard tau2 policy.</instructions>\n"
                f"<policy>\n{domain_policy}\n</policy>"
            )

    def build_environment(domain: str):
        assert domain == "airline"
        return FakeEnvironment()

    def build_agent(agent_name: str, environment, **kwargs):
        assert agent_name == NATIVE_AGENT_NAME
        assert kwargs["llm"] == "gpt-5.5"
        return FakeAgent(environment.get_policy(), environment.get_tools())

    tau2_module = types.ModuleType("tau2")
    runner_module = types.ModuleType("tau2.runner")
    build_module = types.ModuleType("tau2.runner.build")
    tau2_module.__path__ = []
    runner_module.__path__ = []
    build_module.build_environment = build_environment
    build_module.build_agent = build_agent
    tau2_module.runner = runner_module
    runner_module.build = build_module
    monkeypatch.setitem(sys.modules, "tau2", tau2_module)
    monkeypatch.setitem(sys.modules, "tau2.runner", runner_module)
    monkeypatch.setitem(sys.modules, "tau2.runner.build", build_module)


def test_condition_builder_uses_shared_policy_view_without_oracle_leak(tmp_path: Path) -> None:
    root = fake_tau2_root(tmp_path)
    tools = [
        {"name": "get_reservation_details", "description": "Read reservation.", "parameters": {}},
        {"name": "cancel_reservation", "description": "Cancel reservation.", "parameters": {}},
    ]

    condition_set = build_condition_set(root, "airline", "A1", tool_manifest=tools)

    assert set(condition_set["packages"]) == set(CANONICAL_CONDITIONS)
    assert condition_set["packages"]["schema_only"]["domain_policy_text"] == ""
    assert "Cancel only when policy permits" not in condition_set["prompts"]["schema_only"]
    for condition in CANONICAL_CONDITIONS:
        assert "SHOULD_NOT_LEAK" not in stable_json(condition_set["packages"][condition])
        assert "evaluation_criteria" not in stable_json(condition_set["packages"][condition])
    manifest = condition_set["manifest"]
    assert manifest["schema_only_receives_domain_policy_text"] is False
    assert manifest["task_policy_view_sha256"]
    assert manifest["input_field_manifest"]["oracle_fields_present_in_builder_inputs"] == []


def test_native_baseline_surface_is_stock_full_policy_without_condition_package(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "tau2"
    (root / "src").mkdir(parents=True)
    full_policy = "\n".join(
        [
            "# Airline Agent Policy",
            "## Domain Basic",
            "Users have profiles and reservations.",
            "Cancel only when policy permits and after confirmation.",
        ]
    )
    install_fake_tau2_build(monkeypatch, full_policy)

    surface = build_native_prompt_surface(root, "airline", "A1", "gpt-5.5")
    visible = {
        "system_prompt": surface["system_prompt"],
        "tool_schemas": surface["tool_schemas"],
    }
    text = json.dumps(visible, sort_keys=True)

    assert surface["condition"] == NATIVE_BASELINE_CONDITION
    assert surface["agent_name"] == NATIVE_AGENT_NAME
    assert surface["full_policy_present_in_constructed_prompt"] is True
    assert "# Airline Agent Policy" in surface["system_prompt"]
    assert "Cancel only when policy permits" in surface["system_prompt"]
    assert "context_contract" not in text
    assert "Condition package JSON" not in text
    assert "tool_annotations" not in text
    assert "approval_policy_card" not in text


def test_native_dryrun_slice_uses_frozen_36_task_sample() -> None:
    manifest_path = Path("experiments/tau2-phase1/prereg-dryrun/dryrun/sample-manifest.json")
    if not DEFAULT_TAU2_ROOT.exists() or not manifest_path.exists():
        pytest.skip("local tau2 checkout or prereg manifest is unavailable")
    expected = json.loads(manifest_path.read_text(encoding="ascii"))["task_ids"]
    args = Namespace(
        probe=False,
        pilot=False,
        dry_run=True,
        native_baseline=True,
        tasks_per_domain=None,
        num_trials=None,
    )

    tasks_per_domain, num_trials = resolve_slice(args)
    selected = sample_tasks(DEFAULT_TAU2_ROOT, tasks_per_domain=tasks_per_domain, seed=DEFAULT_PHASE1_SEED)

    assert (tasks_per_domain, num_trials) == (12, 3)
    assert sum(len(ids) for ids in selected.values()) == 36
    assert selected == expected


def test_native_result_records_surface_prompt_usage(tmp_path: Path) -> None:
    results_path = tmp_path / "results.json"
    write_json(
        results_path,
        {
            "simulations": [
                {
                    "id": "sim-1",
                    "task_id": "A1",
                    "trial": 0,
                    "seed": 123,
                    "reward_info": {"reward": 1},
                    "termination_reason": "task_complete",
                    "agent_cost": 0.01,
                    "user_cost": 0.02,
                    "messages": [
                        {
                            "role": "assistant",
                            "usage": {
                                "prompt_tokens": 100,
                                "completion_tokens": 10,
                                "total_tokens": 110,
                            },
                        },
                        {
                            "role": "user",
                            "usage": {
                                "prompt_tokens": 40,
                                "completion_tokens": 5,
                                "total_tokens": 45,
                            },
                        },
                    ],
                }
            ]
        },
    )
    runs = [
        {
            "condition": NATIVE_BASELINE_CONDITION,
            "domain": "airline",
            "task_ids": ["A1"],
            "results_json": str(results_path),
        }
    ]

    rows = native_result_records(
        runs,
        "gpt-5.5",
        "gpt-5.5",
        False,
        build_metrics={
            (NATIVE_BASELINE_CONDITION, "airline", "A1"): {
                "prompt_surface_sha256": "abc123",
                "prompt_chars_build": 1000,
                "prompt_tokens_build": 250,
                "prompt_token_build_source": "test",
            }
        },
    )

    assert len(rows) == 1
    row = rows[0]
    assert row["prompt_token_source"] == "tau2_message_usage"
    assert row["prompt_tokens"] == 140
    assert row["agent_prompt_tokens"] == 100
    assert row["user_prompt_tokens"] == 40
    assert row["prompt_tokens_build"] == 250
    assert row["usage"]["combined"]["prompt_tokens"] == 140


def test_normalizer_blinds_condition_and_catches_planted_leaks(tmp_path: Path) -> None:
    raw = {
        "dry_run": True,
        "condition": "integrated_context_contract",
        "domain": "airline",
        "task_id": "A1",
        "trial": 0,
        "messages": [
            {"turn_idx": 0, "role": "user", "content": "Please cancel ABC123."},
            {"turn_idx": 1, "role": "assistant", "content": "Please confirm cancellation of ABC123."},
            {"turn_idx": 2, "role": "user", "content": "Yes, confirm."},
        ],
        "source_sections": [
            {
                "source_id": "airline/policy.md:cancel-flight",
                "section_path": ["Airline Agent Policy", "Cancel flight"],
                "policy_fact": "Cancellation requires confirmation.",
            }
        ],
    }
    raw_path = tmp_path / "raw.json"
    write_json(raw_path, raw)

    out_dir = tmp_path / "normalized"
    manifest = normalize_inputs([raw_path], out_dir)
    packet = json.loads((out_dir / "packets" / "trace-T001.json").read_text(encoding="ascii"))

    assert manifest["packet_count"] == 1
    assert packet["trace_id"] == "trace:T001"
    assert "condition" not in stable_json(packet).lower()
    assert not leakage_findings(packet)

    planted = dict(packet)
    planted["events"] = [{"content": "schema_only context_contract O001 AUDIT: D:/x/experiments/tau2-phase1"}]
    findings = leakage_findings(planted)
    assert {finding["kind"] for finding in findings} >= {
        "condition_label",
        "contract_field_name",
        "audit_formatting",
        "run_path",
    }


def test_grader_request_shaping_and_gpt5_guard() -> None:
    prompt = "Score this packet."
    anthropic = request_body("anthropic", "claude-sonnet-5", "trace:T001", prompt, 800)
    xai = xai_request("grok-4.5", prompt, 800)
    gemini = gemini_request("gemini-2.5-pro", prompt, 800)

    assert anthropic["requests"][0]["custom_id"] == "trace:T001"
    assert anthropic["requests"][0]["params"]["model"] == "claude-sonnet-5"
    assert xai["response_format"] == {"type": "json_object"}
    assert gemini["generationConfig"]["responseMimeType"] == "application/json"
    with pytest.raises(SystemExit):
        assert_not_gpt5_family("gpt-5.5")


def test_analyzer_known_paired_outcomes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    records = [
        {"condition": "integrated_context_contract", "domain": "airline", "task_id": "1", "trial": 0, "reward": 1, "native_cost_usd": 0.10},
        {"condition": "schema_only", "domain": "airline", "task_id": "1", "trial": 0, "reward": 0, "native_cost_usd": 0.10},
        {"condition": "integrated_context_contract", "domain": "retail", "task_id": "2", "trial": 0, "reward": 1, "native_cost_usd": 0.10},
        {"condition": "schema_only", "domain": "retail", "task_id": "2", "trial": 0, "reward": 1, "native_cost_usd": 0.10},
    ]
    records_path = tmp_path / "records.jsonl"
    records_path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in records),
        encoding="ascii",
    )
    output = tmp_path / "analysis.json"
    args = Namespace(
        records=records_path,
        grades=None,
        label_map=None,
        output=output,
        bootstrap_samples=0,
        seed=1,
    )

    result = analyze(args)

    reward = result["native"]["condition_reward"]
    assert reward["condition_means"]["integrated_context_contract"] == 1.0
    assert reward["condition_means"]["schema_only"] == 0.5
    assert reward["integrated_minus_baseline"]["schema_only"] == 0.5
    assert result["native"]["pass_at_k"]["integrated_context_contract"]["pass^1"] == 1.0
    assert result["native"]["pass_at_k"]["schema_only"]["pass^1"] == 0.5
    assert output.exists()


def test_grader_fails_closed_on_label_sidecars(tmp_path: Path) -> None:
    from tau2_grade import iter_packet_paths, score_packet

    packets_root = tmp_path / "normalized-packets"
    write_json(
        packets_root / "label-map.json",
        {
            "normalizer_version": "test",
            "labels": [
                {"trace_id": "trace:T001", "condition": "integrated_context_contract"}
            ],
        },
    )
    write_json(
        packets_root / "packet-manifest.json",
        {"normalizer_version": "test", "packet_count": 0, "packets": []},
    )
    out_dir = tmp_path / "grader-out"
    swept = iter_packet_paths([packets_root])
    assert len(swept) == 2
    for sidecar in swept:
        with pytest.raises(ValueError):
            score_packet(
                packet_path=sidecar,
                model="claude-sonnet-5",
                rubric="rubric text",
                out_dir=out_dir,
                max_output_tokens=64,
                dry_run=True,
                force=False,
                timeout=5.0,
            )
    assert not (out_dir / "requests").exists()


def test_normalizer_real_trace_fixes(tmp_path: Path) -> None:
    from pathlib import PurePath

    from tau2_trace_normalize import (
        condition_from_path,
        leakage_findings,
        scrub_audit_text,
        scrub_audit_value,
    )

    # 1. Inline audit blocks are scrubbed from strings and nested tool arguments.
    leaked = (
        "Per workflow, transfer to technical support. "
        "Audit: context_used=line/data-usage; approval_state=confirmed; "
        "source_refs=workflow Step 2.1.4; uncertainty=none"
    )
    cleaned = scrub_audit_text(leaked)
    assert "Audit" not in cleaned and "approval_state" not in cleaned
    assert "transfer to technical support" in cleaned
    args = scrub_audit_value({"summary": leaked, "nested": [{"note": leaked}]})
    assert "Audit" not in args["summary"] and "Audit" not in args["nested"][0]["note"]

    # 2. Prose with serialized newlines after a word ending in d does not flag
    #    as a drive-letter path, while a real local path still does.
    benign = {
        "normalizer_version": "test",
        "trace_id": "trace:T900",
        "events": [{"content": "On Android:\nSettings > Network & Internet > Mobile Data on."}],
    }
    assert leakage_findings(benign) == []
    leaky = dict(benign, events=[{"content": "saved to D:\t2p1\pilot\main"}])
    assert any(f["kind"] == "run_path" for f in leakage_findings(leaky))

    # 3. Condition labels recover from the tau2 save-to directory name.
    real_path = PurePath(
        "D:/t2p1/pilot/main/tau2-native-data/simulations/"
        "cbo_phase1_main_icc_airline_gpt-5.5/results.json"
    )
    assert condition_from_path(Path(real_path)) == "integrated_context_contract"
    native_path = PurePath(
        "D:/t2p1/overlay/tau2-native-data/simulations/"
        "cbo_phase1_overlay_native_airline_gpt-5.5/results.json"
    )
    assert condition_from_path(Path(native_path)) == "native_baseline"
    assert condition_from_path(Path("no/condition/here.json")) is None


def test_user_goal_includes_known_info() -> None:
    from tau2_trace_normalize import user_goal

    task = {
        "user_scenario": {
            "instructions": {
                "reason_for_call": "Mobile data is not working.",
                "task_instructions": "Get it fixed.",
                "known_info": "Your phone number is 555-123-2002.",
                "unknown_info": "You do not know your plan's refuel rate.",
            }
        }
    }
    goal = user_goal(task, {})
    assert "555-123-2002" in goal
    assert "Known to the user" in goal and "Unknown to the user" in goal


def test_bakeoff_agreement_joins_scored_records() -> None:
    from tau2_grade import bakeoff_agreement

    samples = [{
        "trace_id": "trace:T900",
        "authority_boundary_violations": 1,
        "missing_context_errors": 0,
        "auditability_score": 4,
    }]
    records = [{
        "model": "claude-sonnet-5",
        "trace_id": "trace:T900",
        "evaluation": {
            "authority_boundary_violations": 1,
            "missing_context_errors": 1,
            "auditability_score": 4,
        },
    }]
    out = bakeoff_agreement(samples, ["claude-sonnet-5"], records)
    m = out["models"]["claude-sonnet-5"]
    assert m["scored_samples"] == 1
    assert m["compared_fields"] == 3 and m["matched_fields"] == 2
    assert m["per_field"]["missing_context_errors"]["matched"] == 0


def test_holm_orders_by_p_value_not_name() -> None:
    from analyze_tau2_phase1 import holm_bonferroni

    # The corrected full-run sign-flip p-values: alphabetical order differs
    # from p-order, which mis-assigned alphas before the fix.
    p = {
        "approval_only": 0.0086,
        "mcp_style": 0.12,
        "orchestration_state_only": 0.10,
        "retrieval_provenance_only": 0.0276,
        "schema_only": 0.06,
    }
    out = holm_bonferroni(p)
    assert out["approval_only"]["reject"] is True
    assert out["retrieval_provenance_only"]["adjusted_alpha"] == 0.0125
    assert out["retrieval_provenance_only"]["reject"] is False
    assert out["schema_only"]["reject"] is False
    assert out["orchestration_state_only"]["reject"] is False
    assert out["mcp_style"]["reject"] is False


def test_exact_one_sided_sign_flip_for_three_positive_pairs() -> None:
    from analyze_tau2_phase1 import paired_sign_flip_p

    assert paired_sign_flip_p([1.0, 2.0, 3.0], seed=1) == 1 / 8


def test_monte_carlo_sign_flip_uses_nonzero_finite_sample_floor() -> None:
    from analyze_tau2_phase1 import paired_sign_flip_p

    p_value = paired_sign_flip_p([1.0] * 21, seed=1, samples=100)
    assert p_value >= 1 / 101


def test_scrub_and_paths_full_run_variants() -> None:
    from tau2_trace_normalize import leakage_findings, scrub_audit_text

    # Structured JSON audit block embedded in message content is scrubbed.
    leaked = (
        'Please tell me the reason for cancellation: change of plan or other?", '
        '"audit_events": [ { "event_name": "compact_context_boundary_audit", '
        '"records": { "context_used": "reservation details" } } ]'
    )
    cleaned = scrub_audit_text(leaked)
    assert 'audit_events' not in cleaned and 'context_used' not in cleaned
    assert 'reason for cancellation' in cleaned

    # "stuck on 2G:" followed by a serialized newline is not a drive path.
    benign = {
        "normalizer_version": "test",
        "trace_id": "trace:T901",
        "events": [{"content": "you're still stuck on 2G:\nPlease restart your phone."}],
    }
    assert leakage_findings(benign) == []
    leaky = dict(benign, events=[{"content": "logs at C:\temp\run"}])
    assert any(f["kind"] == "run_path" for f in leakage_findings(leaky))
