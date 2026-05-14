from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from math_model.graph import build_conflict_edges, color_conflict_graph
from math_model.grouping import REFERENCE_GROUPS_D003, evaluate_scheme, generate_schemes, groups_to_rows
from math_model.io import load_teams
from math_model.lottery import draw_from_hash
from math_model.tournament import match_counts


def test_load_teams_reads_final_dataset() -> None:
    teams = load_teams(ROOT / "data" / "final_teams.csv")

    assert len(teams) == 64
    assert teams[0].name == "杭州市"
    assert sum(1 for team in teams if team.level == "city") == 11


def test_conflict_graph_has_expected_size_and_11_coloring() -> None:
    teams = load_teams(ROOT / "data" / "final_teams.csv")
    edges = build_conflict_edges(teams)
    coloring = color_conflict_graph(teams, edges, color_count=11)

    assert len(edges) == 232
    assert coloring is not None
    assert set(coloring.values()) <= set(range(1, 12))
    for a, b in edges:
        assert coloring[a] != coloring[b]


def test_reference_d003_grouping_is_feasible() -> None:
    teams = load_teams(ROOT / "data" / "final_teams.csv")
    rows = groups_to_rows(REFERENCE_GROUPS_D003, teams)
    metrics = evaluate_scheme(REFERENCE_GROUPS_D003, teams)

    assert len(rows) == 64
    assert metrics["hard_violations"] == 0
    assert metrics["same_city_repeat_index"] == 0
    assert metrics["pair_conflict_index"] == 0
    assert metrics["geo_cover"] >= 3.5


def test_generated_grouping_candidates_are_feasible() -> None:
    teams = load_teams(ROOT / "data" / "final_teams.csv")
    schemes = generate_schemes(teams, candidates=20, seed=2026, steps=30)

    assert len(schemes) == 20
    assert all(scheme["hard_violations"] == 0 for scheme in schemes)


def test_public_lottery_hash_rule_is_reproducible() -> None:
    draw = draw_from_hash(
        pool_sha256="c8edf836d1c77bfe7d4ef1765819dc748463ad8f90aec415526d9586fc70b799",
        public_seed="7392048615",
        pool_size=100,
    )

    assert draw.public_random_number == 91954185948163988665075136196978624808181846815307495688921861128068341180838
    assert draw.selected_index == 39


def test_tournament_match_counts_cover_required_formats() -> None:
    counts = match_counts()

    assert counts["现行 16 组单循环 + 32 强"]["total_matches"] == 127
    assert counts["小组双循环 + 32 强"]["total_matches"] == 223
    assert counts["瑞士轮 4 轮 + 32 强"]["total_matches"] == 159
