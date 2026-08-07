from __future__ import annotations

import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from analyze_legacy_profiles import (  # noqa: E402
    bootstrap_profile_ci,
    bootstrap_run_level_ci,
    exact_sign_flip_p,
    holm_bonferroni,
    metric_cells,
    task_profile,
)


def test_profile_resampling_widens_clustered_interval() -> None:
    profiles = {
        "low-a": [0.0] * 50,
        "low-b": [0.0] * 50,
        "high-a": [10.0] * 50,
        "high-b": [10.0] * 50,
    }
    runs = [value for values in profiles.values() for value in values]

    run_ci = bootstrap_run_level_ci(runs, samples=4_000, seed=20260709)
    profile_ci = bootstrap_profile_ci(profiles, samples=4_000, seed=20260709)

    run_width = run_ci[1] - run_ci[0]
    profile_width = profile_ci[1] - profile_ci[0]
    assert profile_width > run_width * 2


def test_holm_orders_by_p_value_not_hypothesis_name() -> None:
    p_values = {
        "alpha_alphabetical_first": 0.040,
        "beta": 0.001,
        "gamma": 0.020,
    }

    corrected = holm_bonferroni(p_values)

    assert corrected["beta"]["rank"] == 1
    assert corrected["beta"]["alpha_threshold"] == 0.016667
    assert corrected["beta"]["reject"] is True
    assert corrected["gamma"]["rank"] == 2
    assert corrected["gamma"]["reject"] is True
    assert corrected["alpha_alphabetical_first"]["rank"] == 3
    assert corrected["alpha_alphabetical_first"]["reject"] is True


def test_catalog_sizes_cluster_to_four_tasks_with_exact_one_sided_floor() -> None:
    records = [
        {
            "catalog_size": size,
            "condition": condition,
            "task_id": f"task-{task}",
            "value": float(condition == "reference"),
        }
        for task in range(4)
        for size in (10, 50, 100, 200)
        for condition in ("reference", "baseline")
    ]
    cells = metric_cells(
        records,
        conditions=("reference", "baseline"),
        profile_key=task_profile,
        metric=lambda row: row["value"],
    )

    assert len(cells["reference"]) == 4
    effects = [
        sum(cells["reference"][task]) / len(cells["reference"][task])
        - sum(cells["baseline"][task]) / len(cells["baseline"][task])
        for task in sorted(cells["reference"])
    ]
    assert exact_sign_flip_p(effects) == 1 / 16
