"""Task-scoped service views.

This module consolidates the large-service focused-view mechanism from
``scripts/run_live_experiment.py`` into a reusable fisheye selector. The default
degree-of-interest score is intentionally simple and replaceable.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
import re
from typing import Any

from .contract import ContextContract


CatalogItem = Mapping[str, Any]
Task = Mapping[str, Any] | str
Scorer = Callable[[CatalogItem, Task, ContextContract], float]

TOKEN_RE = re.compile(r"[a-zA-Z0-9_]+")


def focused_view(
    catalog: Sequence[CatalogItem],
    task: Task,
    contract: ContextContract,
    k: int | None = 5,
    *,
    scorer: Scorer | None = None,
) -> list[dict[str, Any]]:
    """Return the top-k task-scoped catalog entries.

    The result preserves the original item fields and adds ``_doi_score`` for
    inspection. Ties are resolved by stable catalog order, then by item name.
    """

    if k is not None and k < 1:
        raise ValueError("k must be positive or None")
    active_scorer = scorer or default_scorer
    ranked: list[tuple[float, int, str, dict[str, Any]]] = []
    for index, raw_item in enumerate(catalog):
        item = dict(raw_item)
        name = str(item.get("name", item.get("operation", index)))
        score = float(active_scorer(item, task, contract))
        item["_doi_score"] = score
        ranked.append((score, -index, name, item))
    ranked.sort(key=lambda row: (-row[0], -row[1], row[2]))
    selected = ranked if k is None else ranked[:k]
    return [item for _, _, _, item in selected]


def default_scorer(item: CatalogItem, task: Task, contract: ContextContract) -> float:
    """Compute a transparent degree-of-interest score.

    ``DOI(x) = importance(x) - distance(x, focus)`` is operationalized as
    metadata importance plus term and required-tool matches, minus a small
    distance penalty for catalog entries that share no task terms.
    """

    task_terms = terms_for_task(task)
    item_terms = terms_for_item(item)
    overlap = task_terms & item_terms
    required = required_tool_names(task)
    name = str(item.get("name", item.get("operation", "")))
    required_match = 1 if name in required else 0
    importance = float(item.get("importance", 0.0) or 0.0)
    if required_match:
        importance += 8.0
    importance += 1.5 * len(overlap)
    obligation_bonus = obligation_term_bonus(item, contract)
    distance = 0.0 if required_match else max(0.0, 3.0 - len(overlap))
    return importance + obligation_bonus - distance


def terms_for_task(task: Task) -> set[str]:
    """Extract task-focus terms from common task fields."""

    if isinstance(task, str):
        return tokenize(task)
    values: list[Any] = []
    for key in ("task_id", "title", "scenario", "description", "domain"):
        if key in task:
            values.append(task[key])
    for key in ("keywords", "catalog_search_terms", "required_tools"):
        value = task.get(key)
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
            values.extend(value)
    return tokenize(" ".join(str(value) for value in values))


def required_tool_names(task: Task) -> set[str]:
    """Return exact tool names declared as required by the task."""

    if not isinstance(task, Mapping):
        return set()
    value = task.get("required_tools", [])
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return set()
    return {str(item) for item in value}


def terms_for_item(item: CatalogItem) -> set[str]:
    """Extract searchable terms from a catalog item."""

    values: list[Any] = []
    for key in ("name", "operation", "group", "description", "risk"):
        if key in item:
            values.append(item[key])
    for key in ("tags", "keywords", "inputs", "outputs"):
        value = item.get(key)
        if isinstance(value, Mapping):
            values.extend(value.keys())
            values.extend(value.values())
        elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
            values.extend(value)
    return tokenize(" ".join(str(value) for value in values))


def obligation_term_bonus(item: CatalogItem, contract: ContextContract) -> float:
    """Lightly raise tools named by contract preconditions."""

    name = str(item.get("name", item.get("operation", "")))
    bonus = 0.0
    for axis in (
        contract.required_context,
        contract.authority,
        contract.provenance,
        contract.memory,
        contract.privacy,
        contract.uncertainty,
        contract.output_audit,
    ):
        if name in axis.preconditions:
            bonus += 1.0
    return bonus


def tokenize(value: str) -> set[str]:
    """Lowercase tokenization for the default scorer."""

    return {match.group(0).lower() for match in TOKEN_RE.finditer(value)}
