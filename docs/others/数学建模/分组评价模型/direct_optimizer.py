#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Direct optimizer for the Zhejiang city-county football grouping problem.

This script does not first generate a large candidate pool and then rank it.
Instead, it keeps every intermediate scheme feasible and uses simulated
annealing / local search to directly improve a weighted multi-indicator
objective. It is therefore a direct search for high-quality feasible schemes,
not an exhaustive proof of global optimality.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
from copy import deepcopy
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

from group_evaluator import (
    CITY_ORDER,
    DEFAULT_AHP_WEIGHTS,
    GROUP_NAMES,
    METRIC_DIRECTIONS,
    combined_weights,
    evaluate_scheme,
    generate_candidate_schemes,
    load_teams,
    positive_normalize,
    scheme_key,
    scheme_to_named,
    topsis_scores,
    write_scheme_csv,
)


# The scale constants map raw indicators into [0, 1]-like utilities.
# They are not constraints; they express the level at which a cost starts to
# become visibly large under the current indicator system.
COST_SCALES = {
    "same_city_repeat_index": 1.0,
    "pair_conflict_index": 1.0,
    "sport_variance": 700.0,
    "sport_range": 90.0,
    "eco_cv": 0.65,
    "pop_cv": 0.45,
    "tour_cv": 0.32,
    "avg_inner_distance_km": 175.0,
}

BENEFIT_SCALES = {
    "admin_diversity": 4.0,
    "competition_suspense": 0.20,
    "hot_match_index": 850.0,
    "geo_cover": 4.0,
}


def hard_strict_feasible(groups: Sequence[Sequence[str]], teams_by_id: Dict[str, object]) -> bool:
    row = evaluate_scheme(groups, list(teams_by_id.values()))
    if row["hard_violations"] != 0:
        return False
    return row["same_city_repeat_index"] == 0 and row["pair_conflict_index"] == 0


def metric_utility(metric: str, value: float) -> float:
    if metric in COST_SCALES:
        return 1.0 / (1.0 + max(value, 0.0) / COST_SCALES[metric])
    if metric in BENEFIT_SCALES:
        if metric in {"admin_diversity", "geo_cover"}:
            return min(max(value / BENEFIT_SCALES[metric], 0.0), 1.0)
        return 1.0 - math.exp(-max(value, 0.0) / BENEFIT_SCALES[metric])
    raise KeyError(metric)


def direct_score(metrics: Dict[str, float]) -> float:
    if metrics["hard_violations"] != 0:
        return -1e9
    # Normalize AHP weights over the indicators used by the direct objective.
    total_weight = sum(DEFAULT_AHP_WEIGHTS[m] for m in METRIC_DIRECTIONS)
    score = 0.0
    for metric in METRIC_DIRECTIONS:
        score += DEFAULT_AHP_WEIGHTS[metric] / total_weight * metric_utility(metric, metrics[metric])
    return score


def county_positions(groups: Sequence[Sequence[str]], teams_by_id: Dict[str, object]) -> List[Tuple[int, int]]:
    positions = []
    for g_idx, group in enumerate(groups):
        for pos, team_id in enumerate(group):
            if teams_by_id[team_id].level == "county":
                positions.append((g_idx, pos))
    return positions


def can_place(
    team_id: str,
    group_idx: int,
    groups: Sequence[Sequence[str]],
    teams_by_id: Dict[str, object],
    ignore_ids: set[str],
) -> bool:
    team = teams_by_id[team_id]
    if group_idx < 11 and CITY_ORDER[group_idx] == team.parent_city:
        return False
    for other_id in groups[group_idx]:
        if other_id in ignore_ids:
            continue
        other = teams_by_id[other_id]
        if other.parent_city == team.parent_city:
            return False
    return True


def random_swap_neighbor(
    groups: Sequence[Sequence[str]],
    teams_by_id: Dict[str, object],
    rng: random.Random,
    max_trials: int = 80,
) -> List[List[str]] | None:
    positions = county_positions(groups, teams_by_id)
    for _ in range(max_trials):
        g1, p1 = rng.choice(positions)
        g2, p2 = rng.choice(positions)
        if g1 == g2:
            continue
        team1 = groups[g1][p1]
        team2 = groups[g2][p2]
        if not can_place(team1, g2, groups, teams_by_id, ignore_ids={team2}):
            continue
        if not can_place(team2, g1, groups, teams_by_id, ignore_ids={team1}):
            continue
        neighbor = [list(group) for group in groups]
        neighbor[g1][p1], neighbor[g2][p2] = neighbor[g2][p2], neighbor[g1][p1]
        return neighbor
    return None


def random_three_cycle_neighbor(
    groups: Sequence[Sequence[str]],
    teams_by_id: Dict[str, object],
    rng: random.Random,
    max_trials: int = 80,
) -> List[List[str]] | None:
    positions = county_positions(groups, teams_by_id)
    for _ in range(max_trials):
        selected = rng.sample(positions, 3)
        group_ids = {g for g, _ in selected}
        if len(group_ids) < 3:
            continue
        (g1, p1), (g2, p2), (g3, p3) = selected
        t1, t2, t3 = groups[g1][p1], groups[g2][p2], groups[g3][p3]
        if not can_place(t1, g2, groups, teams_by_id, ignore_ids={t2}):
            continue
        if not can_place(t2, g3, groups, teams_by_id, ignore_ids={t3}):
            continue
        if not can_place(t3, g1, groups, teams_by_id, ignore_ids={t1}):
            continue
        neighbor = [list(group) for group in groups]
        neighbor[g2][p2] = t1
        neighbor[g3][p3] = t2
        neighbor[g1][p1] = t3
        return neighbor
    return None


def add_elite(
    elites: Dict[str, Dict[str, object]],
    groups: Sequence[Sequence[str]],
    metrics: Dict[str, float],
    score: float,
    keep: int,
) -> None:
    key = scheme_key(groups)
    if key in elites and elites[key]["direct_score"] >= score:
        return
    item = dict(metrics)
    item["direct_score"] = score
    item["groups"] = [list(group) for group in groups]
    elites[key] = item
    if len(elites) > keep * 8:
        ranked = sorted(elites.items(), key=lambda kv: kv[1]["direct_score"], reverse=True)
        elites.clear()
        elites.update(ranked[: keep * 4])


def optimize(
    teams,
    starts: int,
    steps: int,
    keep: int,
    seed: int,
    initial_pool: int,
) -> List[Dict[str, object]]:
    rng = random.Random(seed)
    teams_by_id = {team.team_id: team for team in teams}
    initial_schemes = generate_candidate_schemes(
        teams=teams,
        count=max(starts, initial_pool),
        seed=seed,
        strict_no_same_city=True,
    )
    if not initial_schemes:
        raise RuntimeError("failed to generate initial feasible schemes")

    elites: Dict[str, Dict[str, object]] = {}
    for start_idx in range(starts):
        current = deepcopy(initial_schemes[start_idx % len(initial_schemes)])
        current_metrics = evaluate_scheme(current, teams)
        current_score = direct_score(current_metrics)
        add_elite(elites, current, current_metrics, current_score, keep)

        best_local = deepcopy(current)
        best_local_score = current_score
        t0 = 0.020
        t1 = 0.001
        for step in range(steps):
            temperature = t0 * (t1 / t0) ** (step / max(steps - 1, 1))
            if rng.random() < 0.82:
                neighbor = random_swap_neighbor(current, teams_by_id, rng)
            else:
                neighbor = random_three_cycle_neighbor(current, teams_by_id, rng)
            if neighbor is None:
                continue
            neighbor_metrics = evaluate_scheme(neighbor, teams)
            neighbor_score = direct_score(neighbor_metrics)
            delta = neighbor_score - current_score
            if delta >= 0 or rng.random() < math.exp(delta / max(temperature, 1e-9)):
                current = neighbor
                current_metrics = neighbor_metrics
                current_score = neighbor_score
                add_elite(elites, current, current_metrics, current_score, keep)
                if current_score > best_local_score:
                    best_local = deepcopy(current)
                    best_local_score = current_score
        best_metrics = evaluate_scheme(best_local, teams)
        add_elite(elites, best_local, best_metrics, best_local_score, keep)

    ranked = sorted(elites.values(), key=lambda item: item["direct_score"], reverse=True)
    return ranked[:keep]


def write_direct_comparison(path: Path, rows: Sequence[Dict[str, object]], teams) -> None:
    lines = [
        "# 直接寻优得到的若干可行方案",
        "",
        "这些方案由模拟退火/局部搜索直接优化综合目标得到，不依赖先生成大规模候选池后统一排序。所有方案均满足硬约束和同市县级队不重复条件。",
        "",
        "## 指标对比",
        "",
        "| 排名 | 方案 | 直接目标值 | TOPSIS得分 | 实力方差 | 实力极差 | 竞争悬念 | 热点指数 | 经济CV | 人口CV | 文旅CV | 平均距离km | 地域覆盖 |",
        "|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for rank, row in enumerate(rows, start=1):
        lines.append(
            "| "
            + " | ".join(
                [
                    str(rank),
                    str(row["scheme_id"]),
                    f"{row['direct_score']:.6f}",
                    f"{row['elite_topsis']:.6f}",
                    f"{row['sport_variance']:.2f}",
                    f"{row['sport_range']:.2f}",
                    f"{row['competition_suspense']:.6f}",
                    f"{row['hot_match_index']:.2f}",
                    f"{row['eco_cv']:.4f}",
                    f"{row['pop_cv']:.4f}",
                    f"{row['tour_cv']:.4f}",
                    f"{row['avg_inner_distance_km']:.2f}",
                    f"{row['geo_cover']:.4f}",
                ]
            )
            + " |"
        )
    for rank, row in enumerate(rows, start=1):
        named = scheme_to_named(row["groups"], teams)
        lines.extend(["", f"## 直接寻优方案 {rank}：{row['scheme_id']}", "", "| 小组 | 队伍 |", "|---|---|"])
        for group_name in GROUP_NAMES:
            lines.append(f"| {group_name} | {'、'.join(named[group_name])} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Directly optimize feasible grouping schemes.")
    parser.add_argument("--teams", type=Path, default=Path("data/teams.csv"))
    parser.add_argument("--starts", type=int, default=40, help="multi-start count")
    parser.add_argument("--steps", type=int, default=4000, help="local search steps per start")
    parser.add_argument("--keep", type=int, default=5, help="number of final schemes to output")
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--initial-pool", type=int, default=80, help="small feasible seed pool for multi-start")
    parser.add_argument("--output-dir", type=Path, default=Path("outputs_direct"))
    args = parser.parse_args()

    teams = load_teams(args.teams)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    rows = optimize(
        teams=teams,
        starts=args.starts,
        steps=args.steps,
        keep=args.keep,
        seed=args.seed,
        initial_pool=args.initial_pool,
    )
    for idx, row in enumerate(rows, start=1):
        row["scheme_id"] = f"D{idx:03d}"

    z_rows = positive_normalize(rows, list(METRIC_DIRECTIONS.keys()))
    weights = combined_weights(z_rows, list(METRIC_DIRECTIONS.keys()), alpha=0.5)
    topsis = topsis_scores(z_rows, list(METRIC_DIRECTIONS.keys()), weights)
    for row, score in zip(rows, topsis):
        row["elite_topsis"] = score

    ranking_path = args.output_dir / "direct_ranking.csv"
    with ranking_path.open("w", encoding="utf-8-sig", newline="") as f:
        fieldnames = [
            "rank",
            "scheme_id",
            "direct_score",
            "elite_topsis",
            "hard_violations",
            *METRIC_DIRECTIONS.keys(),
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for rank, row in enumerate(rows, start=1):
            writer.writerow({name: row.get(name, rank if name == "rank" else "") for name in fieldnames})

    write_direct_comparison(args.output_dir / "direct_top_schemes.md", rows, teams)
    write_scheme_csv(args.output_dir / "direct_best_scheme.csv", rows[0]["groups"], teams)
    serializable = []
    for row in rows:
        item = {key: value for key, value in row.items() if key != "groups"}
        item["groups"] = scheme_to_named(row["groups"], teams)
        serializable.append(item)
    (args.output_dir / "direct_top_schemes.json").write_text(
        json.dumps(serializable, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"Direct optimization finished: starts={args.starts}, steps={args.steps}")
    print(f"Best direct scheme: {rows[0]['scheme_id']}, direct_score={rows[0]['direct_score']:.6f}")
    print(f"Wrote: {ranking_path}")
    print(f"Wrote: {args.output_dir / 'direct_top_schemes.md'}")


if __name__ == "__main__":
    main()
