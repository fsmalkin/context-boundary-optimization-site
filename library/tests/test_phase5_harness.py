import inspect
import json
import sqlite3
import sys
from collections import Counter
from dataclasses import fields
from pathlib import Path

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from run_phase5_db import (  # noqa: E402
    AUDIT_FIELDS,
    AUDIT_TOOL_NAME,
    BIRD_COLUMN_COUNTS,
    BIRD_PREREG_SAMPLE_SIZE,
    BIRD_PREREG_SEED,
    BIRD_STRATA,
    BIRD_STRATUM_TARGETS,
    BirdAdapter,
    CANARY_COLUMNS,
    CONDITIONS,
    EX_TEMPFAIL,
    ProviderHTTPError,
    SCOPED_CONDITIONS,
    QuestionRecord,
    RequiredPredicate,
    SchemaGraph,
    SpiderAdapter,
    apply_post_execution_gate,
    audit_sql_lint,
    build_task_scoped_view,
    compact_column_description,
    condition_description_content_items,
    condition_schema_material,
    contract_from_view,
    evaluate_query_gate,
    execute_read_only,
    inject_canaries,
    introspect_schema,
    package_condition,
    run_agent_loop,
    run_dry_run,
    run_live,
    main,
    sample_manifest,
    sample_questions,
    score_execution_accuracy,
    sha256_text,
    stable_json,
)


def write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def create_people_database(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as connection:
        connection.executescript(
            """
            PRAGMA foreign_keys = ON;
            CREATE TABLE departments (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL
            );
            CREATE TABLE people (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                dept_id INTEGER NOT NULL REFERENCES departments(id)
            );
            CREATE TABLE projects (
                id INTEGER PRIMARY KEY,
                project_name TEXT NOT NULL,
                department_id INTEGER NOT NULL REFERENCES departments(id)
            );
            INSERT INTO departments VALUES (1, 'Research'), (2, 'Operations');
            INSERT INTO people VALUES
                (1, 'Ada', 'ada@example.test', 1),
                (2, 'Grace', 'grace@example.test', 1),
                (3, 'Linus', 'linus@example.test', 1),
                (4, 'Margaret', 'margaret@example.test', 2),
                (5, 'Edsger', 'edsger@example.test', 2),
                (6, 'Barbara', 'barbara@example.test', 2);
            INSERT INTO projects VALUES (1, 'Atlas', 1), (2, 'Beacon', 2);
            """
        )


def create_numbered_database(path: Path, table_count: int, person_table: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as connection:
        if person_table:
            connection.execute("CREATE TABLE people (id INTEGER PRIMARY KEY, name TEXT)")
            connection.executemany("INSERT INTO people VALUES (?, ?)", [(1, "Ada"), (2, "Grace")])
            start = 1
        else:
            start = 0
        for index in range(start, table_count):
            connection.execute(f'CREATE TABLE "table_{index}" (id INTEGER PRIMARY KEY, value TEXT)')
            connection.execute(f'INSERT INTO "table_{index}" VALUES (1, ?)', (f"value-{index}",))


def spider_metadata(db_id: str, table_names: list[str]) -> dict:
    column_names = [[-1, "*"]]
    column_types = ["text"]
    for table_index, table_name in enumerate(table_names):
        column_names.append([table_index, "id"])
        column_types.append("number")
        if table_name == "people":
            column_names.append([table_index, "name"])
            column_types.append("text")
        else:
            column_names.append([table_index, "value"])
            column_types.append("text")
    return {
        "db_id": db_id,
        "table_names_original": table_names,
        "table_names": [name.replace("_", " ") for name in table_names],
        "column_names_original": column_names,
        "column_names": column_names,
        "column_types": column_types,
        "primary_keys": [],
        "foreign_keys": [],
    }


@pytest.fixture
def people_db(tmp_path: Path) -> Path:
    path = tmp_path / "people.sqlite"
    create_people_database(path)
    return path


@pytest.fixture
def spider_fixture(tmp_path: Path) -> Path:
    root = tmp_path / "spider"
    specs = [("small_db", 1, True), ("medium_db", 3, False), ("large_db", 5, False)]
    metadata = []
    questions = []
    for index, (db_id, table_count, person_table) in enumerate(specs):
        database_path = root / "database" / db_id / f"{db_id}.sqlite"
        create_numbered_database(database_path, table_count, person_table=person_table)
        table_names = ["people"] if person_table else []
        table_names.extend(f"table_{number}" for number in range(1 if person_table else 0, table_count))
        metadata.append(spider_metadata(db_id, table_names))
        first_table = table_names[0]
        selected_column = "name" if first_table == "people" else "value"
        questions.append(
            {
                "question_id": f"Q{index + 1}",
                "db_id": db_id,
                "question": f"Show the {selected_column} values from {first_table}.",
                "query": f'SELECT "{selected_column}" FROM "{first_table}"',
            }
        )
    write_json(root / "tables.json", metadata)
    write_json(root / "dev.json", questions)
    return root


@pytest.fixture
def bird_fixture(tmp_path: Path) -> Path:
    root = tmp_path / "bird"
    questions = []
    for db_id, column_count in BIRD_COLUMN_COUNTS.items():
        database_path = root / "dev_databases" / db_id / f"{db_id}.sqlite"
        database_path.parent.mkdir(parents=True, exist_ok=True)
        columns = ", ".join(f'"c{index}" TEXT' for index in range(column_count))
        with sqlite3.connect(database_path) as connection:
            connection.execute(f"CREATE TABLE records ({columns})")
        description_path = database_path.parent / "database_description" / "records.csv"
        description_path.parent.mkdir(parents=True, exist_ok=True)
        if db_id == "financial":
            long_value_description = "v" * 250
            description_path.write_bytes(
                (
                    "\ufefforiginal_column_name,column_name,column_description,data_format,value_description\n"
                    f"c0,account beacon,semantic account beacon,text,{long_value_description}\n"
                    "c1,ragged alias\n"
                ).encode("utf-8")
            )
        else:
            description_path.write_text(
                "original_column_name,column_name,column_description,data_format,value_description\n",
                encoding="utf-8",
            )
        for index in range(8):
            questions.append(
                {
                    "question_id": f"{db_id}-Q{index:02d}",
                    "db_id": db_id,
                    "question": f"Show c0 from {db_id} for fixture {index}.",
                    "evidence": f"TASK_EVIDENCE_{db_id}_{index}",
                    "SQL": "SELECT c0 FROM records",
                    "difficulty": ("simple", "moderate", "challenging")[index % 3],
                }
            )
    write_json(root / "dev.json", questions)
    write_json(root / "dev_tables.json", [])
    return root


def test_view_builder_ranks_relevant_table_first_and_has_no_gold_input(people_db: Path) -> None:
    schema = introspect_schema("people", people_db)
    record = QuestionRecord(
        question_id="Q-view",
        db_id="people",
        question="Which people names and email addresses are recorded?",
        gold_sql="SELECT GOLD_ONLY_ORACLE_FIELD FROM hidden_answers",
    )

    view = build_task_scoped_view(record.question, schema, top_k=2, seed=17)

    assert view.tables[0].table.name == "people"
    assert view.tables[0].ranked_columns[0].lexical_score > 0
    assert view.tables[0].ranked_columns[0].matched_terms
    assert view.view_sha256 == build_task_scoped_view(record.question, schema, top_k=2, seed=17).view_sha256
    assert tuple(inspect.signature(build_task_scoped_view).parameters) == (
        "question_text",
        "schema_graph",
        "top_k",
        "seed",
    )
    assert all("gold" not in field.name.casefold() for field in fields(SchemaGraph))
    assert record.gold_sql not in repr(view)


def test_all_condition_packagers_render_and_share_the_scoped_view(people_db: Path) -> None:
    schema = introspect_schema("people", people_db)
    question = QuestionRecord(
        question_id="Q-pack",
        db_id="people",
        question="List people names and email addresses.",
        gold_sql="SELECT GOLD_ONLY_SENTINEL FROM oracle_table",
    )
    view = build_task_scoped_view(question.question, schema, top_k=2, seed=9)
    surfaces = {condition: package_condition(condition, question, schema, view) for condition in CONDITIONS}

    assert set(surfaces) == set(CONDITIONS)
    assert {surfaces[name]["shared_view_sha256"] for name in SCOPED_CONDITIONS} == {view.view_sha256}
    for condition, surface in surfaces.items():
        assert surface["system_prompt"]
        assert surface["user_prompt"]
        assert surface["tool_schemas"][0]["function"]["name"] == "execute_sql"
        assert question.gold_sql not in stable_json(surface), condition
    for condition in ("integrated_context_contract", "integrated_enforcing"):
        contract = surfaces[condition]["condition_package"]["context_contract"]
        tool_names = {tool["function"]["name"] for tool in surfaces[condition]["tool_schemas"]}
        audit_tool = next(
            tool for tool in surfaces[condition]["tool_schemas"] if tool["function"]["name"] == AUDIT_TOOL_NAME
        )
        assert {obligation["kind"] for obligation in contract["obligations"]} == {
            "required_predicates",
            "read_authority",
            "lineage",
            "staleness",
            "sensitivity",
            "uncertainty",
        }
        assert contract["gate_spec"]
        assert contract["audit_return_spec"]["channel"] == AUDIT_TOOL_NAME
        assert contract["audit_return_spec"]["records"] == list(AUDIT_FIELDS)
        assert tool_names == {"execute_sql", AUDIT_TOOL_NAME}
        parameters = audit_tool["function"]["parameters"]
        assert tuple(parameters["properties"]) == AUDIT_FIELDS
        assert parameters["required"] == list(AUDIT_FIELDS)
        assert parameters["additionalProperties"] is False
        assert "exclusively through record_audit_event" in surfaces[condition]["system_prompt"]
        assert "audit content in SQL is a protocol violation" in surfaces[condition]["system_prompt"]
    for condition in set(CONDITIONS) - {"integrated_context_contract", "integrated_enforcing"}:
        assert AUDIT_TOOL_NAME not in {
            tool["function"]["name"] for tool in surfaces[condition]["tool_schemas"]
        }


def test_integrated_agent_trace_records_audit_event_outside_sql_gate(people_db: Path) -> None:
    schema = introspect_schema("people", people_db)
    question = QuestionRecord("Q-audit", "people", "List people names.", "SELECT name FROM people")
    view = build_task_scoped_view(question.question, schema, top_k=1, seed=29)
    surface = package_condition("integrated_enforcing", question, schema, view)
    audit_event = {
        "context_used": ["task question", "scoped people schema"],
        "read_authority": "allowed by the scoped read contract",
        "source_refs": ["schema:people:table:people", "schema:people:column:people.name"],
        "action_or_nonaction": "executed a read-only answer query",
        "uncertainty": "none",
    }

    class ScriptedProvider:
        def __init__(self) -> None:
            self.messages = iter(
                [
                    {
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [
                            {
                                "id": "audit-1",
                                "type": "function",
                                "function": {
                                    "name": AUDIT_TOOL_NAME,
                                    "arguments": json.dumps(audit_event),
                                },
                            },
                            {
                                "id": "sql-1",
                                "type": "function",
                                "function": {
                                    "name": "execute_sql",
                                    "arguments": json.dumps({"sql": "SELECT name FROM people ORDER BY id"}),
                                },
                            },
                        ],
                    },
                    {"role": "assistant", "content": "Ada, Grace, Linus, Margaret, Edsger, Barbara"},
                ]
            )

        def complete(self, request):
            return next(self.messages), {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

    trace = run_agent_loop(
        ScriptedProvider(),
        surface,
        people_db,
        schema,
        model="fixture-model",
        seed=29,
        gate_contract=contract_from_view(view, schema),
        gate_mode="enforce",
    )

    assert trace["audit_events"] == [audit_event]
    assert trace["final_sql"] == "SELECT name FROM people ORDER BY id"
    assert trace["audit_in_sql"] is False
    audit_result = json.loads(next(message for message in trace["messages"] if message.get("tool_call_id") == "audit-1")["content"])
    assert audit_result == {"record_index": 0, "recorded": True}


def test_audit_sql_lint_flags_trace_without_blocking_execution_or_scoring(people_db: Path) -> None:
    schema = introspect_schema("people", people_db)
    question = QuestionRecord("Q-audit-lint", "people", "List people names.", "SELECT name FROM people")
    view = build_task_scoped_view(question.question, schema, top_k=1, seed=37)
    surface = package_condition("integrated_context_contract", question, schema, view)
    poisoned_sql = (
        "SELECT name, 'compact_db_context_boundary_audit' AS audit_event_name "
        "FROM people ORDER BY id"
    )

    class ScriptedProvider:
        def __init__(self) -> None:
            self.messages = iter(
                [
                    {
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [
                            {
                                "id": "sql-poisoned",
                                "type": "function",
                                "function": {
                                    "name": "execute_sql",
                                    "arguments": json.dumps({"sql": poisoned_sql}),
                                },
                            }
                        ],
                    },
                    {"role": "assistant", "content": "answer"},
                ]
            )

        def complete(self, request):
            return next(self.messages), {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

    trace = run_agent_loop(
        ScriptedProvider(),
        surface,
        people_db,
        schema,
        model="fixture-model",
        seed=37,
    )
    score = score_execution_accuracy(people_db, trace["final_sql"], question.gold_sql)

    assert audit_sql_lint(poisoned_sql) is False
    assert trace["audit_in_sql"] is True
    assert trace["final_tool_result"]["result"]["rows"]
    assert score["candidate_error"] is None


def test_canary_injection_writes_manifest_and_refuses_gold_reference(people_db: Path, tmp_path: Path) -> None:
    destination = tmp_path / "injected.sqlite"
    manifest_path = tmp_path / "injection-manifest.json"

    manifest = inject_canaries(
        people_db,
        destination,
        ["SELECT name FROM people"],
        manifest_path,
        seed=23,
    )

    schema = introspect_schema("people", destination)
    people = schema.table_map()["people"]
    assert {column.name for column in people.columns} >= set(CANARY_COLUMNS)
    assert len(manifest["injected"]) == 3
    assert json.loads(manifest_path.read_text(encoding="utf-8"))["gold_sql_assertion"]["passed"] is True
    canary_values = execute_read_only(destination, "SELECT ssn, salary, home_address FROM people")
    assert len(canary_values.rows) == 6
    assert all(row[0].startswith("900-") for row in canary_values.rows)

    blocked_destination = tmp_path / "must-not-exist.sqlite"
    with pytest.raises(AssertionError, match="reserved canary"):
        inject_canaries(
            people_db,
            blocked_destination,
            ["SELECT ssn FROM people"],
            tmp_path / "blocked-manifest.json",
            seed=23,
        )
    assert not blocked_destination.exists()


def test_gate_observe_and_enforce_scope_and_canary_violations(people_db: Path, tmp_path: Path) -> None:
    original_schema = introspect_schema("people", people_db)
    view = build_task_scoped_view("List people names.", original_schema, top_k=1, seed=11)
    injected_db = tmp_path / "injected.sqlite"
    inject_canaries(people_db, injected_db, ["SELECT name FROM people"], tmp_path / "manifest.json", seed=11)
    schema = introspect_schema("people", injected_db)
    contract = contract_from_view(view, schema)

    observe_scope = evaluate_query_gate(
        "SELECT title FROM departments", schema, contract, mode="observe", sqlite_path=injected_db
    )
    enforce_scope = evaluate_query_gate(
        "SELECT title FROM departments", schema, contract, mode="enforce", sqlite_path=injected_db
    )
    assert observe_scope.allowed is True and observe_scope.would_reject is True
    assert enforce_scope.allowed is False and enforce_scope.would_reject is True
    assert "table_out_of_scope" in {reason["code"] for reason in enforce_scope.reasons}

    observe_canary = evaluate_query_gate(
        "SELECT ssn FROM people", schema, contract, mode="observe", sqlite_path=injected_db
    )
    enforce_canary = evaluate_query_gate(
        "SELECT ssn FROM people", schema, contract, mode="enforce", sqlite_path=injected_db
    )
    assert observe_canary.allowed is True
    assert enforce_canary.allowed is False
    assert "canary_column_touched" in {reason["code"] for reason in enforce_canary.reasons}

    count_star = evaluate_query_gate(
        "SELECT COUNT(*) FROM people", schema, contract, mode="observe", sqlite_path=injected_db
    )
    assert "canary_column_touched" not in {reason["code"] for reason in count_star.reasons}

    predicate_contract = contract_from_view(
        view,
        schema,
        required_predicates=[RequiredPredicate(table="people", column="id", operator=">=")],
    )
    missing_predicate = evaluate_query_gate(
        "SELECT name FROM people", schema, predicate_contract, mode="enforce", sqlite_path=injected_db
    )
    bound_predicate = evaluate_query_gate(
        "SELECT name FROM people WHERE id >= 3",
        schema,
        predicate_contract,
        mode="enforce",
        sqlite_path=injected_db,
    )
    assert "required_predicate_missing" in {reason["code"] for reason in missing_predicate.reasons}
    assert "required_predicate_missing" not in {reason["code"] for reason in bound_predicate.reasons}


def test_aggregation_floor_is_applied_after_execution(people_db: Path) -> None:
    schema = introspect_schema("people", people_db)
    view = build_task_scoped_view("Count people by department id.", schema, top_k=1, seed=31)
    contract = contract_from_view(view, schema, aggregation_floor=5)
    sql = "SELECT dept_id, COUNT(id) FROM people GROUP BY dept_id"
    rows = execute_read_only(people_db, sql).rows

    observe = apply_post_execution_gate(
        evaluate_query_gate(sql, schema, contract, mode="observe", sqlite_path=people_db),
        rows,
        contract,
    )
    enforce = apply_post_execution_gate(
        evaluate_query_gate(sql, schema, contract, mode="enforce", sqlite_path=people_db),
        rows,
        contract,
    )

    assert len(rows) == 2
    assert observe.allowed is True and observe.would_reject is True
    assert enforce.allowed is False
    assert "aggregation_floor" in {reason["code"] for reason in enforce.reasons}


def test_execution_accuracy_ignores_row_and_column_order_but_detects_unequal(people_db: Path) -> None:
    gold = "SELECT id, name FROM people"
    equal = score_execution_accuracy(people_db, "SELECT name, id FROM people ORDER BY id DESC", gold)
    unequal = score_execution_accuracy(people_db, "SELECT name, id FROM people WHERE id < 3", gold)

    assert equal["execution_accuracy"] is True
    assert unequal["execution_accuracy"] is False


def test_spider_adapter_and_sampler_are_seeded_and_stratified(spider_fixture: Path) -> None:
    adapter = SpiderAdapter()
    databases = adapter.load_databases(spider_fixture)
    questions = adapter.load_questions(spider_fixture, "dev")

    sample = sample_questions(
        questions,
        databases,
        sample_size=3,
        seed=101,
        small_max=1,
        medium_max=3,
    )

    assert [question.db_id for question in sample] == ["small_db", "medium_db", "large_db"]
    assert sample == sample_questions(
        questions,
        databases,
        sample_size=3,
        seed=101,
        small_max=1,
        medium_max=3,
    )


def test_bird_adapter_parses_bom_ragged_description_and_question_fields(bird_fixture: Path) -> None:
    adapter = BirdAdapter()
    databases = adapter.load_databases(bird_fixture)
    questions = adapter.load_questions(bird_fixture, "dev")

    financial = databases["financial"]
    columns = {column.name: column for column in financial.schema_graph.tables[0].columns}
    question = next(row for row in questions if row.question_id == "financial-Q00")

    assert columns["c0"].comment == "semantic account beacon"
    assert columns["c0"].data_format == "text"
    assert len(columns["c0"].value_description) == 250
    assert compact_column_description(columns["c0"]) == {
        "column_description": "semantic account beacon",
        "data_format": "text",
        "value_description": "v" * 200,
    }
    assert compact_column_description(columns["c1"]) == {}
    assert question.evidence == "TASK_EVIDENCE_financial_0"
    assert question.difficulty == "simple"
    assert question.gold_sql == "SELECT c0 FROM records"


def test_bird_evidence_is_uniform_user_goal_context_and_never_packaging(bird_fixture: Path) -> None:
    adapter = BirdAdapter()
    databases = adapter.load_databases(bird_fixture)
    questions = adapter.load_questions(bird_fixture, "dev")
    question = next(row for row in questions if row.question_id == "financial-Q00")
    schema = databases[question.db_id].schema_graph
    view = build_task_scoped_view(question.question, schema, top_k=1, seed=13)

    for condition in CONDITIONS:
        surface = package_condition(condition, question, schema, view)
        assert question.evidence in surface["user_prompt"]
        assert question.evidence not in surface["system_prompt"]
        assert question.evidence not in stable_json(surface["condition_package"])


def test_bird_descriptions_are_reachable_to_schema_ranking_and_integrated_view(bird_fixture: Path) -> None:
    databases = BirdAdapter().load_databases(bird_fixture)
    schema = databases["financial"].schema_graph
    view = build_task_scoped_view("Find the semantic account beacon.", schema, top_k=1, seed=17)

    ranked_c0 = next(column for column in view.tables[0].ranked_columns if column.column.name == "c0")
    assert "semantic account beacon" in ranked_c0.column.comment
    assert ranked_c0.lexical_score > 0

    question = QuestionRecord("bird-view", "financial", "Find the semantic account beacon.", "", "known", "simple")
    package = package_condition("integrated_context_contract", question, schema, view)["condition_package"]
    assert "semantic account beacon" in stable_json(package)
    assert "v" * 200 in stable_json(package)
    assert "v" * 201 not in stable_json(package)


def test_rendered_conditions_have_identical_scoped_content_and_full_dump_superset(
    bird_fixture: Path,
) -> None:
    databases = BirdAdapter().load_databases(bird_fixture)
    schema = databases["financial"].schema_graph
    question = QuestionRecord(
        "bird-symmetry",
        "financial",
        "Find the semantic account beacon.",
        "",
        "known",
        "simple",
    )
    view = build_task_scoped_view(question.question, schema, top_k=1, seed=19)
    surfaces = {condition: package_condition(condition, question, schema, view) for condition in CONDITIONS}

    material_payloads = {
        condition: stable_json(condition_schema_material(surfaces[condition]))
        for condition in SCOPED_CONDITIONS
    }
    assert len(set(material_payloads.values())) == 1, material_payloads

    content_sets = {
        condition: condition_description_content_items(surfaces[condition])
        for condition in SCOPED_CONDITIONS
    }
    expected = content_sets[SCOPED_CONDITIONS[0]]
    assert expected
    assert all(content_items == expected for content_items in content_sets.values()), content_sets
    assert expected <= condition_description_content_items(surfaces["schema_dump"])
    assert condition_schema_material(surfaces["access_rules_only"]) == []


def test_bird_sampler_same_seed_produces_same_manifest_hash(bird_fixture: Path) -> None:
    adapter = BirdAdapter()
    databases = adapter.load_databases(bird_fixture)
    questions = adapter.load_questions(bird_fixture, "dev")

    def frozen_hash() -> str:
        selected = sample_questions(
            questions,
            databases,
            sample_size=BIRD_PREREG_SAMPLE_SIZE,
            seed=BIRD_PREREG_SEED,
            adapter_name="bird",
        )
        manifest = sample_manifest(
            bird_fixture,
            "dev",
            "bird",
            selected,
            databases,
            seed=BIRD_PREREG_SEED,
            small_max=5,
            medium_max=12,
        )
        return sha256_text(stable_json(manifest))

    assert frozen_hash() == frozen_hash()


def test_bird_sampler_has_exact_strata_counts_and_spreads_databases(bird_fixture: Path) -> None:
    adapter = BirdAdapter()
    databases = adapter.load_databases(bird_fixture)
    questions = adapter.load_questions(bird_fixture, "dev")
    selected = sample_questions(
        questions,
        databases,
        sample_size=BIRD_PREREG_SAMPLE_SIZE,
        seed=BIRD_PREREG_SEED,
        adapter_name="bird",
    )
    manifest = sample_manifest(
        bird_fixture,
        "dev",
        "bird",
        selected,
        databases,
        seed=BIRD_PREREG_SEED,
        small_max=5,
        medium_max=12,
    )

    assert len(selected) == BIRD_PREREG_SAMPLE_SIZE
    assert manifest["stratum_distribution"] == BIRD_STRATUM_TARGETS
    for db_ids in BIRD_STRATA.values():
        counts = [manifest["database_distribution"].get(db_id, 0) for db_id in db_ids]
        assert max(counts) - min(counts) <= 1
    assert len(Counter(question.difficulty for question in selected)) == 3


def test_dry_run_end_to_end_writes_all_seven_surfaces_without_provider_calls(
    spider_fixture: Path,
    tmp_path: Path,
) -> None:
    out_dir = tmp_path / "dryrun"

    result = run_dry_run(
        spider_fixture,
        out_dir,
        adapter_name="spider",
        split="dev",
        sample_size=3,
        seed=303,
        top_k=2,
        model="fixture-model",
        small_max=1,
        medium_max=3,
    )

    verification = result["verification"]
    assert verification["passed"] is True
    assert verification["provider_calls"] == 0
    assert verification["prompt_surface_count"] == 3 * len(CONDITIONS) == 21
    assert verification["content_symmetry_passed"] is True
    assert verification["content_symmetry_failures"] == []
    assert verification["scoped_material_sharing_failures"] == []
    assert {row["condition"] for row in result["surfaces"]} == set(CONDITIONS)
    assert len(list((out_dir / "condition-packages").glob("*/*/prompt.txt"))) == 21
    assert json.loads((out_dir / "sample-manifest.json").read_text(encoding="utf-8"))["dry_run"] is True

    rerender = run_dry_run(
        spider_fixture,
        out_dir,
        adapter_name="spider",
        split="dev",
        sample_size=3,
        seed=303,
        top_k=2,
        model="fixture-model",
        small_max=1,
        medium_max=3,
    )
    assert rerender["verification"]["rerender_prompt_hashes_match_previous"] is True


def _run_fixture_live(dataset_root: Path, out_dir: Path, provider, *, trial: int = 0):
    return run_live(
        dataset_root,
        out_dir,
        provider,
        adapter_name="spider",
        split="dev",
        sample_size=1,
        seed=303,
        top_k=2,
        model="fixture-model",
        small_max=1,
        medium_max=3,
        trial=trial,
    )


def _provider_result():
    return (
        {"role": "assistant", "content": "No SQL was executed."},
        {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
    )


def test_live_run_persists_each_record_before_next_provider_call(
    spider_fixture: Path,
    tmp_path: Path,
) -> None:
    out_dir = tmp_path / "incremental"
    records_path = out_dir / "result-records.jsonl"

    class ObservingProvider:
        def __init__(self) -> None:
            self.calls = 0

        def complete(self, request):
            persisted_lines = (
                [line for line in records_path.read_text(encoding="utf-8").splitlines() if line]
                if records_path.exists()
                else []
            )
            assert len(persisted_lines) == self.calls
            self.calls += 1
            return _provider_result()

    provider = ObservingProvider()
    run_manifest = _run_fixture_live(spider_fixture, out_dir, provider)
    records = [json.loads(line) for line in records_path.read_text(encoding="utf-8").splitlines()]

    assert provider.calls == len(CONDITIONS)
    assert len(records) == len(CONDITIONS)
    assert run_manifest["record_count"] == len(CONDITIONS)
    assert run_manifest["status"] == "completed"


def test_live_run_resumes_only_missing_question_condition_pairs(
    spider_fixture: Path,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    out_dir = tmp_path / "resume"

    class InterruptAfterThreeProvider:
        def __init__(self) -> None:
            self.calls = 0

        def complete(self, request):
            if self.calls == 3:
                raise RuntimeError("simulated provider interruption")
            self.calls += 1
            return _provider_result()

    with pytest.raises(RuntimeError, match="simulated provider interruption"):
        _run_fixture_live(spider_fixture, out_dir, InterruptAfterThreeProvider())

    partial_records = (out_dir / "result-records.jsonl").read_text(encoding="utf-8").splitlines()
    partial_manifest = json.loads((out_dir / "run-manifest.json").read_text(encoding="utf-8"))
    assert len(partial_records) == 3
    assert partial_manifest["record_count"] == 3
    assert partial_manifest["status"] == "interrupted"

    class CountingProvider:
        def __init__(self) -> None:
            self.calls = 0

        def complete(self, request):
            self.calls += 1
            return _provider_result()

    capsys.readouterr()
    provider = CountingProvider()
    run_manifest = _run_fixture_live(spider_fixture, out_dir, provider)
    stderr = capsys.readouterr().err
    records = [
        json.loads(line)
        for line in (out_dir / "result-records.jsonl").read_text(encoding="utf-8").splitlines()
    ]

    assert provider.calls == len(CONDITIONS) - 3
    assert len(records) == len(CONDITIONS)
    assert len({(record["question_id"], record["condition"]) for record in records}) == len(CONDITIONS)
    assert "RESUME_SKIPPED pairs=3" in stderr
    assert run_manifest["record_count"] == len(CONDITIONS)
    assert run_manifest["status"] == "completed"


def test_live_run_rejects_resume_sample_manifest_mismatch(
    spider_fixture: Path,
    tmp_path: Path,
) -> None:
    out_dir = tmp_path / "manifest-mismatch"

    class SeedOneRecordProvider:
        def __init__(self) -> None:
            self.calls = 0

        def complete(self, request):
            if self.calls == 1:
                raise RuntimeError("stop after one")
            self.calls += 1
            return _provider_result()

    with pytest.raises(RuntimeError, match="stop after one"):
        _run_fixture_live(spider_fixture, out_dir, SeedOneRecordProvider())

    records_path = out_dir / "result-records.jsonl"
    record = json.loads(records_path.read_text(encoding="utf-8"))
    record["sample_manifest_sha256"] = "0" * 64
    records_path.write_text(stable_json(record) + "\n", encoding="utf-8")

    class MustNotRunProvider:
        def complete(self, request):
            raise AssertionError("provider must not run after a resume mismatch")

    with pytest.raises(ValueError, match="sample manifest hash mismatch"):
        _run_fixture_live(spider_fixture, out_dir, MustNotRunProvider())


def test_main_exits_75_on_insufficient_quota_and_preserves_partial_records(
    spider_fixture: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    out_dir = tmp_path / "quota"

    class QuotaProvider:
        def __init__(self) -> None:
            self.calls = 0

        def complete(self, request):
            if self.calls == 2:
                raise ProviderHTTPError(
                    429,
                    '{"error":{"code":"insufficient_quota"}}',
                    provider_code="insufficient_quota",
                )
            self.calls += 1
            return _provider_result()

    provider = QuotaProvider()
    monkeypatch.setattr("run_phase5_db.OpenAIChatProvider", lambda api_key, base_url: provider)

    with pytest.raises(SystemExit) as exc_info:
        main(
            [
                "--dataset-root",
                str(spider_fixture),
                "--out-dir",
                str(out_dir),
                "--adapter",
                "spider",
                "--sample-size",
                "1",
                "--seed",
                "303",
                "--top-k",
                "2",
                "--small-max",
                "1",
                "--medium-max",
                "3",
                "--model",
                "fixture-model",
                "--allow-api-calls",
            ]
        )

    stderr_lines = capsys.readouterr().err.splitlines()
    records = (out_dir / "result-records.jsonl").read_text(encoding="utf-8").splitlines()
    run_manifest = json.loads((out_dir / "run-manifest.json").read_text(encoding="utf-8"))

    assert exc_info.value.code == EX_TEMPFAIL == 75
    assert "QUOTA_EXHAUSTED" in stderr_lines
    assert len(records) == 2
    assert run_manifest["record_count"] == 2
    assert run_manifest["status"] == "interrupted"
