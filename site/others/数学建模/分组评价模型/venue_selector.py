#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Venue selection and group assignment for problem 3.

Input:
  - data/teams.csv
  - outputs_direct/direct_best_scheme.csv

Output:
  - outputs_venues/venue_solution.md
  - outputs_venues/venue_assignment.csv
  - outputs_venues/venue_metrics.json
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
from dataclasses import asdict
from pathlib import Path
from collections import Counter
from typing import Dict, List, Sequence, Tuple

from group_evaluator import Team, haversine_km, load_teams, normalize_by_team


REGION_MIN = {
    "浙北": 1,
    "浙东": 1,
    "浙中": 1,
    "浙南": 1,
    "浙西": 1,
    "浙西南": 1,
}

PREFERRED_SEEDS = ["杭州市", "宁波市", "温州市", "嘉兴市", "义乌市", "衢州市", "台州市", "丽水市"]


def read_groups(path: Path) -> Dict[str, List[str]]:
    groups: Dict[str, List[str]] = {}
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            groups.setdefault(row["group"], []).append(row["team_id"])
    return groups


def impact_scores(teams: Sequence[Team]) -> Dict[str, float]:
    gdp = normalize_by_team(teams, "gdp")
    pop = normalize_by_team(teams, "population")
    tour = normalize_by_team(teams, "tourism")
    sport = normalize_by_team(teams, "sports_investment")
    return {
        t.team_id: 0.30 * pop[t.team_id] + 0.30 * gdp[t.team_id] + 0.25 * tour[t.team_id] + 0.15 * sport[t.team_id]
        for t in teams
    }


def eligible_candidates(teams: Sequence[Team], max_candidates: int) -> List[Team]:
    scores = impact_scores(teams)
    by_name = {t.name: t for t in teams}
    selected = {by_name[name].team_id for name in PREFERRED_SEEDS if name in by_name}

    # Keep all city-level teams, high-impact county/city venues, and regional bests.
    for t in teams:
        if t.level == "city":
            selected.add(t.team_id)

    for region in sorted({t.region for t in teams}):
        region_teams = [t for t in teams if t.region == region]
        for t in sorted(region_teams, key=lambda x: scores[x.team_id], reverse=True)[:3]:
            selected.add(t.team_id)

    remaining = [t for t in teams if t.team_id not in selected]
    for t in sorted(remaining, key=lambda x: scores[x.team_id], reverse=True):
        if len(selected) >= max_candidates:
            break
        selected.add(t.team_id)

    return [t for t in teams if t.team_id in selected]


def std(values: Sequence[float]) -> float:
    mean = sum(values) / len(values)
    return math.sqrt(sum((x - mean) ** 2 for x in values) / len(values))


def group_venue_features(groups: Dict[str, List[str]], teams_by_id: Dict[str, Team], venues: Sequence[Team]) -> Dict[Tuple[str, str], dict]:
    features = {}
    for group_name, team_ids in groups.items():
        group_teams = [teams_by_id[tid] for tid in team_ids]
        for venue in venues:
            distances = [haversine_km(team, venue) for team in group_teams]
            home_penalty = 0
            for team in group_teams:
                if team.name == venue.name:
                    home_penalty = 1
                elif team.parent_city == venue.parent_city:
                    home_penalty = max(home_penalty, 0.5)
            features[(group_name, venue.team_id)] = {
                "avg_distance": sum(distances) / len(distances),
                "std_distance": std(distances),
                "max_distance": max(distances),
                "home_penalty": home_penalty,
            }
    return features


def minmax(values: Sequence[float]) -> Tuple[float, float]:
    return min(values), max(values)


def normalize_cost(value: float, lo: float, hi: float) -> float:
    if math.isclose(lo, hi):
        return 0.0
    return (value - lo) / (hi - lo)


def normalize_benefit(value: float, lo: float, hi: float) -> float:
    if math.isclose(lo, hi):
        return 0.0
    return (hi - value) / (hi - lo)


def assignment_costs(groups: Dict[str, List[str]], teams: Sequence[Team], venues: Sequence[Team], profile: str = "balanced") -> Dict[Tuple[str, str], float]:
    teams_by_id = {t.team_id: t for t in teams}
    features = group_venue_features(groups, teams_by_id, venues)
    impacts = impact_scores(teams)
    avg_lo, avg_hi = minmax([x["avg_distance"] for x in features.values()])
    std_lo, std_hi = minmax([x["std_distance"] for x in features.values()])
    max_lo, max_hi = minmax([x["max_distance"] for x in features.values()])
    impact_values = [impacts[v.team_id] for v in venues]
    imp_lo, imp_hi = minmax(impact_values)

    costs = {}
    for group_name in groups:
        for venue in venues:
            f = features[(group_name, venue.team_id)]
            group_attention = 0.0
            group_team_ids = groups[group_name]
            for tid in group_team_ids:
                team = teams_by_id[tid]
                if team.name == venue.name:
                    group_attention += impacts[tid]
                elif team.parent_city == venue.parent_city:
                    group_attention += 0.5 * impacts[tid]
            avg_c = normalize_cost(f["avg_distance"], avg_lo, avg_hi)
            std_c = normalize_cost(f["std_distance"], std_lo, std_hi)
            max_c = normalize_cost(f["max_distance"], max_lo, max_hi)
            impact_c = normalize_benefit(impacts[venue.team_id], imp_lo, imp_hi)
            home_bonus = min(group_attention, 1.0)
            if profile == "fair":
                costs[(group_name, venue.team_id)] = (
                    0.38 * avg_c
                    + 0.20 * std_c
                    + 0.14 * max_c
                    + 0.10 * f["home_penalty"]
                    + 0.18 * impact_c
                )
            else:
                costs[(group_name, venue.team_id)] = (
                    0.32 * avg_c
                    + 0.17 * std_c
                    + 0.12 * max_c
                    + 0.08 * f["home_penalty"]
                    + 0.15 * impact_c
                    - 0.16 * home_bonus
                )
    return costs


def assign_groups_to_venues(group_names: Sequence[str], selected_venues: Sequence[Team], costs: Dict[Tuple[str, str], float]) -> Tuple[float, Dict[str, str]]:
    venue_ids = [v.team_id for v in selected_venues]
    ordered_groups = list(group_names)
    memo: Dict[Tuple[int, Tuple[int, ...]], Tuple[float, Tuple[str, ...]]] = {}

    def dp(idx: int, caps: Tuple[int, ...]) -> Tuple[float, Tuple[str, ...]]:
        key = (idx, caps)
        if key in memo:
            return memo[key]
        if idx == len(ordered_groups):
            if all(c == 0 for c in caps):
                return 0.0, ()
            return float("inf"), ()
        g = ordered_groups[idx]
        best = float("inf")
        best_path: Tuple[str, ...] = ()
        for pos, vid in enumerate(venue_ids):
            if caps[pos] <= 0:
                continue
            new_caps = list(caps)
            new_caps[pos] -= 1
            rest_cost, rest_path = dp(idx + 1, tuple(new_caps))
            total = costs[(g, vid)] + rest_cost
            if total < best:
                best = total
                best_path = (vid,) + rest_path
        memo[key] = (best, best_path)
        return memo[key]

    best_cost, path = dp(0, tuple([2] * len(venue_ids)))
    assignment = {g: vid for g, vid in zip(ordered_groups, path)}
    return best_cost, assignment


def region_ok(venues: Sequence[Team]) -> bool:
    counts = {}
    for v in venues:
        counts[v.region] = counts.get(v.region, 0) + 1
    return all(counts.get(region, 0) >= minimum for region, minimum in REGION_MIN.items())


def region_balance_penalty(venues: Sequence[Team]) -> float:
    values = []
    counts = Counter(v.region for v in venues)
    for region in REGION_MIN:
        values.append(counts.get(region, 0))
    mean = sum(values) / len(values)
    return sum((x - mean) ** 2 for x in values) / len(values)


def venue_constraints_ok(venues: Sequence[Team], profile: str) -> bool:
    if not region_ok(venues):
        return False
    if profile == "balanced":
        county_count = sum(1 for v in venues if v.level == "county")
        if not (2 <= county_count <= 3):
            return False
        counts = Counter(v.region for v in venues)
        if any(count > 2 for count in counts.values()):
            return False
    return True


def venue_set_score(venues: Sequence[Team], assign_cost: float, all_teams: Sequence[Team], profile: str = "balanced") -> float:
    impacts = impact_scores(all_teams)
    impact_sum = sum(impacts[v.team_id] for v in venues)
    region_count = len({v.region for v in venues})
    county_count = sum(1 for v in venues if v.level == "county")
    if profile == "fair":
        county_balance_penalty = abs(county_count - 1.5) * 0.04
        return assign_cost - 0.18 * impact_sum - 0.08 * region_count + county_balance_penalty
    county_balance_penalty = 0 if 2 <= county_count <= 3 else 0.7
    return (
        assign_cost
        - 0.20 * impact_sum
        - 0.10 * region_count
        + 0.35 * region_balance_penalty(venues)
        + county_balance_penalty
    )


def optimize_venues(
    groups: Dict[str, List[str]],
    teams: Sequence[Team],
    candidates: Sequence[Team],
    seed: int,
    iterations: int,
    profile: str,
    fixed_names: Sequence[str] | None = None,
) -> Tuple[List[Team], Dict[str, str], float]:
    rng = random.Random(seed)
    by_name = {t.name: t for t in candidates}
    preferred_names = list(fixed_names) if fixed_names else PREFERRED_SEEDS
    preferred = [by_name[name] for name in preferred_names if name in by_name]
    if len(preferred) < 8:
        missing = sorted(set(preferred_names) - set(by_name))
        raise RuntimeError(f"Preferred/fixed venues are not all present in candidate set: {missing}")

    costs = assignment_costs(groups, teams, candidates, profile=profile)
    group_names = sorted(groups)

    def evaluate(selected: Sequence[Team]) -> Tuple[float, Dict[str, str], float]:
        assign_cost, assignment = assign_groups_to_venues(group_names, selected, costs)
        total = venue_set_score(selected, assign_cost, teams, profile=profile)
        if not venue_constraints_ok(selected, profile):
            total += 2.0
        return total, assignment, assign_cost

    best_selected = preferred[:]
    best_score, best_assignment, best_assign_cost = evaluate(best_selected)
    if fixed_names:
        return sorted(best_selected, key=lambda v: v.name), best_assignment, best_score
    current = best_selected[:]
    current_score = best_score

    candidate_ids = {c.team_id for c in candidates}
    for step in range(iterations):
        selected_ids = {v.team_id for v in current}
        out_idx = rng.randrange(len(current))
        available = [c for c in candidates if c.team_id not in selected_ids]
        incoming = rng.choice(available)
        trial = current[:]
        trial[out_idx] = incoming
        if profile == "fair" and sum(1 for v in trial if v.level == "county") == 0:
            continue
        trial_score, trial_assignment, trial_assign_cost = evaluate(trial)
        temperature = 0.08 * (0.002 / 0.08) ** (step / max(iterations - 1, 1))
        if trial_score < current_score or rng.random() < math.exp((current_score - trial_score) / max(temperature, 1e-9)):
            current = trial
            current_score = trial_score
            if trial_score < best_score:
                best_selected = trial[:]
                best_score = trial_score
                best_assignment = trial_assignment
                best_assign_cost = trial_assign_cost

    return sorted(best_selected, key=lambda v: v.name), best_assignment, best_score


def solution_metrics(groups: Dict[str, List[str]], teams: Sequence[Team], venues: Sequence[Team], assignment: Dict[str, str]) -> dict:
    teams_by_id = {t.team_id: t for t in teams}
    venues_by_id = {v.team_id: v for v in venues}
    features = group_venue_features(groups, teams_by_id, venues)
    group_rows = []
    all_distances = []
    home_count = 0.0
    strong_home_count = 0
    home_attention = 0.0
    impacts = impact_scores(teams)
    for group_name in sorted(groups):
        vid = assignment[group_name]
        venue = venues_by_id[vid]
        f = features[(group_name, vid)]
        distances = [haversine_km(teams_by_id[tid], venue) for tid in groups[group_name]]
        all_distances.extend(distances)
        home_count += f["home_penalty"]
        strong_home = False
        for tid in groups[group_name]:
            team = teams_by_id[tid]
            if team.name == venue.name:
                strong_home = True
                home_attention += impacts[tid]
            elif team.parent_city == venue.parent_city:
                home_attention += 0.5 * impacts[tid]
        strong_home_count += 1 if strong_home else 0
        group_rows.append(
            {
                "group": group_name,
                "venue": venue.name,
                "avg_distance": f["avg_distance"],
                "std_distance": f["std_distance"],
                "max_distance": f["max_distance"],
                "home_penalty": f["home_penalty"],
            }
        )
    return {
        "selected_venues": [v.name for v in venues],
        "region_count": len({v.region for v in venues}),
        "regions": sorted({v.region for v in venues}),
        "county_venue_count": sum(1 for v in venues if v.level == "county"),
        "region_balance_penalty": region_balance_penalty(venues),
        "team_avg_distance": sum(all_distances) / len(all_distances),
        "team_max_distance": max(all_distances),
        "group_avg_distance_mean": sum(r["avg_distance"] for r in group_rows) / len(group_rows),
        "group_distance_fairness_mean": sum(r["std_distance"] for r in group_rows) / len(group_rows),
        "home_penalty_sum": home_count,
        "strong_home_group_count": strong_home_count,
        "home_attention_bonus": home_attention,
        "groups": group_rows,
    }


def write_outputs(output_dir: Path, groups: Dict[str, List[str]], teams: Sequence[Team], venues: Sequence[Team], assignment: Dict[str, str], metrics: dict) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    teams_by_id = {t.team_id: t for t in teams}
    venues_by_id = {v.team_id: v for v in venues}

    with (output_dir / "venue_assignment.csv").open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["venue", "region", "host_groups", "group_teams", "avg_distance_km", "max_distance_km"])
        for venue in venues:
            hosted = [g for g, vid in assignment.items() if vid == venue.team_id]
            for g in sorted(hosted):
                row = next(x for x in metrics["groups"] if x["group"] == g)
                team_names = "、".join(teams_by_id[tid].name for tid in groups[g])
                writer.writerow([venue.name, venue.region, g, team_names, f"{row['avg_distance']:.2f}", f"{row['max_distance']:.2f}"])

    (output_dir / "venue_metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# 问题三比赛地点选择结果",
        "",
        "## 选址结果",
        "",
        "| 比赛地点 | 区域 | 承办小组 | 小组队伍 | 平均距离km | 最远距离km |",
        "|---|---|---|---|---:|---:|",
    ]
    for venue in venues:
        hosted = sorted([g for g, vid in assignment.items() if vid == venue.team_id])
        for g in hosted:
            row = next(x for x in metrics["groups"] if x["group"] == g)
            team_names = "、".join(teams_by_id[tid].name for tid in groups[g])
            lines.append(
                f"| {venue.name} | {venue.region} | {g} | {team_names} | {row['avg_distance']:.2f} | {row['max_distance']:.2f} |"
            )

    lines.extend(
        [
            "",
            "## 综合指标",
            "",
            f"- 覆盖区域数：{metrics['region_count']}，覆盖区域：{'、'.join(metrics['regions'])}",
            f"- 县级承办点数量：{metrics['county_venue_count']}",
            f"- 参赛队平均到赛地距离：{metrics['team_avg_distance']:.2f} km",
            f"- 单队最远到赛地距离：{metrics['team_max_distance']:.2f} km",
            f"- 小组平均距离均值：{metrics['group_avg_distance_mean']:.2f} km",
            f"- 小组出行距离标准差均值：{metrics['group_distance_fairness_mean']:.2f} km",
            f"- 主场关联惩罚合计：{metrics['home_penalty_sum']:.2f}",
            f"- 强主场小组数：{metrics['strong_home_group_count']}",
            f"- 主场传播收益：{metrics['home_attention_bonus']:.4f}",
            f"- 区域均衡惩罚：{metrics['region_balance_penalty']:.4f}",
        ]
    )
    (output_dir / "venue_solution.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Select eight venues and assign sixteen groups.")
    parser.add_argument("--teams", type=Path, default=Path("data/teams.csv"))
    parser.add_argument("--groups", type=Path, default=Path("outputs_direct/direct_best_scheme.csv"))
    parser.add_argument("--output-dir", type=Path, default=Path("outputs_venues"))
    parser.add_argument("--max-candidates", type=int, default=30)
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--iterations", type=int, default=6000)
    parser.add_argument("--profile", choices=["fair", "balanced"], default="balanced", help="fair=中立公平优先；balanced=公平-影响力折中")
    parser.add_argument("--fixed-venues", default="", help="comma-separated venue names; if set, only optimize group assignment")
    args = parser.parse_args()

    teams = load_teams(args.teams)
    groups = read_groups(args.groups)
    candidates = eligible_candidates(teams, max_candidates=args.max_candidates)
    fixed_names = [x.strip() for x in args.fixed_venues.split(",") if x.strip()]
    venues, assignment, score = optimize_venues(groups, teams, candidates, args.seed, args.iterations, profile=args.profile, fixed_names=fixed_names or None)
    metrics = solution_metrics(groups, teams, venues, assignment)
    metrics["objective_score"] = score
    metrics["candidate_count"] = len(candidates)
    metrics["profile"] = args.profile
    metrics["fixed_venues"] = fixed_names
    write_outputs(args.output_dir, groups, teams, venues, assignment, metrics)
    print(f"Candidate venues: {len(candidates)}")
    print(f"Selected venues: {', '.join(v.name for v in venues)}")
    print(f"Objective score: {score:.6f}")
    print(f"Average team distance: {metrics['team_avg_distance']:.2f} km")
    print(f"Wrote: {args.output_dir / 'venue_solution.md'}")


if __name__ == "__main__":
    main()
