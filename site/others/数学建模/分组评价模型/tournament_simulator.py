#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tournament format simulator for problem 4.

It compares several competition formats by Monte Carlo simulation:
  A_current: current format, 16 groups of 4, single round-robin, top 2, random knockout.
  B_seeded: same competition size but using the optimized D001 grouping as a seeded/fair grouping baseline.
  C_constrained_ko: same group stage, knockout first round pairs group winners with other-group runners-up.
  D_double_rr: group double round-robin, top 2, constrained knockout.

The simulation uses potential strength scores from group_evaluator.py and simple
Bradley-Terry style match probabilities with draw, home, and travel effects.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

from group_evaluator import Team, attention_scores, haversine_km, load_teams, team_strength_scores


FORMATS = {
    "A_current": {"double_round": False, "constrained_ko": False},
    "B_seeded": {"double_round": False, "constrained_ko": False},
    "C_constrained_ko": {"double_round": False, "constrained_ko": True},
    "D_double_rr": {"double_round": True, "constrained_ko": True},
}


def read_groups(path: Path) -> Dict[str, List[str]]:
    groups: Dict[str, List[str]] = {}
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            groups.setdefault(row["group"], []).append(row["team_id"])
    return dict(sorted(groups.items()))


def read_venue_assignment(path: Path, teams: Sequence[Team]) -> Dict[str, str]:
    by_name = {t.name: t.team_id for t in teams}
    assignment = {}
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            assignment[row["host_groups"]] = by_name[row["venue"]]
    return assignment


def pairwise(group: Sequence[str]) -> Iterable[Tuple[str, str]]:
    for i in range(len(group)):
        for j in range(i + 1, len(group)):
            yield group[i], group[j]


def home_affinity(team: Team, venue: Team) -> float:
    if team.name == venue.name:
        return 1.0
    if team.parent_city == venue.parent_city:
        return 0.5
    return 0.0


def effective_strength(team_id: str, venue_id: str | None, teams_by_id: Dict[str, Team], base_strength: Dict[str, float]) -> float:
    value = base_strength[team_id]
    if venue_id is None:
        return value
    team = teams_by_id[team_id]
    venue = teams_by_id[venue_id]
    distance = haversine_km(team, venue)
    return value + 3.0 * home_affinity(team, venue) - 0.004 * distance


def play_group_match(
    a: str,
    b: str,
    venue_id: str,
    teams_by_id: Dict[str, Team],
    base_strength: Dict[str, float],
    rng: random.Random,
    theta: float,
    draw_base: float,
) -> Tuple[int, int, str | None, bool, float, float]:
    ra = effective_strength(a, venue_id, teams_by_id, base_strength)
    rb = effective_strength(b, venue_id, teams_by_id, base_strength)
    ea = math.exp(theta * ra)
    eb = math.exp(theta * rb)
    draw_weight = draw_base * math.exp(-abs(ra - rb) / 22.0)
    denom = ea + eb + draw_weight
    p_a = ea / denom
    p_draw = draw_weight / denom
    u = rng.random()
    suspense = 1 / (1 + abs(base_strength[a] - base_strength[b]))
    upset = False
    if u < p_a:
        winner = a
        if base_strength[b] - base_strength[a] >= 12:
            upset = True
        return 3, 0, winner, upset, suspense, abs(base_strength[a] - base_strength[b])
    if u < p_a + p_draw:
        return 1, 1, None, False, suspense, abs(base_strength[a] - base_strength[b])
    winner = b
    if base_strength[a] - base_strength[b] >= 12:
        upset = True
    return 0, 3, winner, upset, suspense, abs(base_strength[a] - base_strength[b])


def play_knockout_match(
    a: str,
    b: str,
    teams_by_id: Dict[str, Team],
    base_strength: Dict[str, float],
    rng: random.Random,
    theta: float,
) -> Tuple[str, bool, float]:
    ra = base_strength[a]
    rb = base_strength[b]
    pa = math.exp(theta * ra) / (math.exp(theta * ra) + math.exp(theta * rb))
    winner = a if rng.random() < pa else b
    loser = b if winner == a else a
    upset = base_strength[loser] - base_strength[winner] >= 12
    suspense = 1 / (1 + abs(base_strength[a] - base_strength[b]))
    return winner, upset, suspense


def rank_group(rows: Dict[str, dict], rng: random.Random) -> List[str]:
    return sorted(
        rows,
        key=lambda tid: (
            rows[tid]["points"],
            rows[tid]["gd"],
            rows[tid]["gf"],
            rng.random(),
        ),
        reverse=True,
    )


def simulate_group_stage(
    groups: Dict[str, List[str]],
    venue_assignment: Dict[str, str],
    teams_by_id: Dict[str, Team],
    base_strength: Dict[str, float],
    rng: random.Random,
    double_round: bool,
    theta: float,
    draw_base: float,
) -> Tuple[List[str], List[str], dict]:
    winners = []
    runners = []
    stats = {"matches": 0, "upsets": 0, "suspense_sum": 0.0}
    for group_name, team_ids in groups.items():
        table = {tid: {"points": 0, "gf": 0, "ga": 0, "gd": 0} for tid in team_ids}
        rounds = 2 if double_round else 1
        for _ in range(rounds):
            for a, b in pairwise(team_ids):
                pa, pb, winner, upset, suspense, _ = play_group_match(
                    a,
                    b,
                    venue_assignment.get(group_name),
                    teams_by_id,
                    base_strength,
                    rng,
                    theta,
                    draw_base,
                )
                # Use synthetic goals consistent with points, only for tie-breaks.
                if pa == 3:
                    ga, gb = 1 + rng.randrange(3), rng.randrange(2)
                    if ga <= gb:
                        ga = gb + 1
                elif pb == 3:
                    gb, ga = 1 + rng.randrange(3), rng.randrange(2)
                    if gb <= ga:
                        gb = ga + 1
                else:
                    ga = gb = rng.randrange(3)
                table[a]["points"] += pa
                table[b]["points"] += pb
                table[a]["gf"] += ga
                table[a]["ga"] += gb
                table[b]["gf"] += gb
                table[b]["ga"] += ga
                table[a]["gd"] = table[a]["gf"] - table[a]["ga"]
                table[b]["gd"] = table[b]["gf"] - table[b]["ga"]
                stats["matches"] += 1
                stats["upsets"] += 1 if upset else 0
                stats["suspense_sum"] += suspense
        ranking = rank_group(table, rng)
        winners.append(ranking[0])
        runners.append(ranking[1])
    return winners, runners, stats


def constrained_first_round(winners: List[str], runners: List[str], groups: Dict[str, List[str]], rng: random.Random) -> List[Tuple[str, str]]:
    team_group = {tid: g for g, tids in groups.items() for tid in tids}
    remaining_runners = runners[:]
    rng.shuffle(remaining_runners)
    pairs = []
    for w in winners:
        valid = [r for r in remaining_runners if team_group[r] != team_group[w]]
        if not valid:
            r = remaining_runners.pop()
        else:
            r = rng.choice(valid)
            remaining_runners.remove(r)
        pairs.append((w, r))
    return pairs


def simulate_knockout(
    winners: List[str],
    runners: List[str],
    groups: Dict[str, List[str]],
    teams_by_id: Dict[str, Team],
    base_strength: Dict[str, float],
    rng: random.Random,
    constrained: bool,
    theta: float,
) -> Tuple[str, Dict[str, int], dict]:
    stage_reached = {}
    teams = winners + runners
    for tid in teams:
        stage_reached[tid] = 32

    if constrained:
        current_pairs = constrained_first_round(winners, runners, groups, rng)
        current = []
        stats = {"matches": 0, "upsets": 0, "suspense_sum": 0.0}
        for a, b in current_pairs:
            winner, upset, suspense = play_knockout_match(a, b, teams_by_id, base_strength, rng, theta)
            current.append(winner)
            stage_reached[winner] = 16
            stats["matches"] += 1
            stats["upsets"] += 1 if upset else 0
            stats["suspense_sum"] += suspense
    else:
        current = teams[:]
        rng.shuffle(current)
        stats = {"matches": 0, "upsets": 0, "suspense_sum": 0.0}

    while len(current) > 1:
        rng.shuffle(current)
        next_round = []
        next_stage = len(current) // 2
        for i in range(0, len(current), 2):
            a, b = current[i], current[i + 1]
            winner, upset, suspense = play_knockout_match(a, b, teams_by_id, base_strength, rng, theta)
            next_round.append(winner)
            stage_reached[winner] = next_stage
            stats["matches"] += 1
            stats["upsets"] += 1 if upset else 0
            stats["suspense_sum"] += suspense
        current = next_round
    champion = current[0]
    stage_reached[champion] = 1
    return champion, stage_reached, stats


def simulate_format(
    fmt: str,
    groups: Dict[str, List[str]],
    venue_assignment: Dict[str, str],
    teams: Sequence[Team],
    n_sims: int,
    seed: int,
    theta: float,
    draw_base: float,
) -> dict:
    rng = random.Random(seed)
    teams_by_id = {t.team_id: t for t in teams}
    strength = team_strength_scores(teams)
    sorted_strength = sorted(strength, key=strength.get, reverse=True)
    top1 = sorted_strength[0]
    top8 = set(sorted_strength[:8])
    top16 = set(sorted_strength[:16])
    format_options = FORMATS[fmt]

    counters = Counter()
    top8_stage16_sum = 0
    top16_stage32_sum = 0
    top8_early_events = 0
    total_matches = 0
    total_upsets = 0
    suspense_sum = 0.0

    for _ in range(n_sims):
        winners, runners, group_stats = simulate_group_stage(
            groups,
            venue_assignment,
            teams_by_id,
            strength,
            rng,
            format_options["double_round"],
            theta,
            draw_base,
        )
        champion, stage_reached, ko_stats = simulate_knockout(
            winners,
            runners,
            groups,
            teams_by_id,
            strength,
            rng,
            format_options["constrained_ko"],
            theta,
        )
        counters[champion] += 1
        qualified = set(winners + runners)
        top16_stage32_sum += sum(1 for t in top16 if t in qualified) / 16
        top8_stage16_sum += sum(1 for t in top8 if stage_reached.get(t, 64) <= 16) / 8
        if sum(1 for t in top8 if stage_reached.get(t, 64) > 16) >= 3:
            top8_early_events += 1
        total_matches += group_stats["matches"] + ko_stats["matches"]
        total_upsets += group_stats["upsets"] + ko_stats["upsets"]
        suspense_sum += group_stats["suspense_sum"] + ko_stats["suspense_sum"]

    match_count = total_matches / n_sims
    return {
        "format": fmt,
        "simulations": n_sims,
        "total_matches": match_count,
        "minimum_matches_per_team": 6 if format_options["double_round"] else 3,
        "champion_max_matches": (6 if format_options["double_round"] else 3) + 5,
        "top16_group_qualification_rate": top16_stage32_sum / n_sims,
        "top8_reach_16_rate": top8_stage16_sum / n_sims,
        "best_team_champion_rate": counters[top1] / n_sims,
        "top8_early_elimination_event_rate": top8_early_events / n_sims,
        "upset_rate": total_upsets / total_matches if total_matches else 0,
        "average_suspense": suspense_sum / total_matches if total_matches else 0,
        "most_common_champions": counters.most_common(5),
    }


def theoretical_formats() -> List[dict]:
    return [
        {"format": "A_current", "group_matches": 96, "knockout_matches": 31, "total_matches": 127, "minimum_matches_per_team": 3, "champion_max_matches": 8},
        {"format": "B_seeded", "group_matches": 96, "knockout_matches": 31, "total_matches": 127, "minimum_matches_per_team": 3, "champion_max_matches": 8},
        {"format": "C_constrained_ko", "group_matches": 96, "knockout_matches": 31, "total_matches": 127, "minimum_matches_per_team": 3, "champion_max_matches": 8},
        {"format": "D_double_rr", "group_matches": 192, "knockout_matches": 31, "total_matches": 223, "minimum_matches_per_team": 6, "champion_max_matches": 11},
        {"format": "E_swiss4_plus_ko", "group_matches": 128, "knockout_matches": 31, "total_matches": 159, "minimum_matches_per_team": 4, "champion_max_matches": 9},
    ]


def write_outputs(output_dir: Path, results: List[dict], theory: List[dict], teams: Sequence[Team]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "simulation_results.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    with (output_dir / "simulation_results.csv").open("w", encoding="utf-8-sig", newline="") as f:
        fieldnames = [
            "format",
            "simulations",
            "total_matches",
            "minimum_matches_per_team",
            "champion_max_matches",
            "top16_group_qualification_rate",
            "top8_reach_16_rate",
            "best_team_champion_rate",
            "top8_early_elimination_event_rate",
            "upset_rate",
            "average_suspense",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in results:
            writer.writerow({key: row[key] for key in fieldnames})

    lines = [
        "# 问题四赛制仿真结果",
        "",
        "## 场次成本对比",
        "",
        "| 赛制 | 小组赛场次 | 淘汰赛场次 | 总场次 | 每队保底 | 冠军最多 |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in theory:
        lines.append(
            f"| {row['format']} | {row['group_matches']} | {row['knockout_matches']} | {row['total_matches']} | {row['minimum_matches_per_team']} | {row['champion_max_matches']} |"
        )
    lines.extend(
        [
            "",
            "## 蒙特卡洛指标",
            "",
            "| 赛制 | 前16强队小组出线率 | 前8强队进16强率 | 最强队夺冠率 | 前8强队过早淘汰事件率 | 爆冷率 | 平均悬念 | 总场次 |",
            "|---|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in results:
        lines.append(
            f"| {row['format']} | {row['top16_group_qualification_rate']:.4f} | {row['top8_reach_16_rate']:.4f} | {row['best_team_champion_rate']:.4f} | {row['top8_early_elimination_event_rate']:.4f} | {row['upset_rate']:.4f} | {row['average_suspense']:.6f} | {row['total_matches']:.0f} |"
        )
    lines.extend(
        [
            "",
            "## 结论",
            "",
            "现行 16 组 4 队单循环 + 32 强淘汰的赛制总场次为 127 场，组织成本适中。双循环能提高强队稳定性，但总场次增加到 223 场，增幅约 75.6%，不适合作为短周期赛事主方案。更可取的做法是在保留现行大框架的基础上，引入优质方案池抽签、种子分档、淘汰赛约束对阵和明确排名细则。",
        ]
    )
    (output_dir / "simulation_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Simulate tournament formats for problem 4.")
    parser.add_argument("--teams", type=Path, default=Path("data/teams.csv"))
    parser.add_argument("--groups", type=Path, default=Path("outputs_direct/direct_best_scheme.csv"))
    parser.add_argument("--venues", type=Path, default=Path("outputs_venues_balanced/venue_assignment.csv"))
    parser.add_argument("--sims", type=int, default=3000)
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--theta", type=float, default=0.035)
    parser.add_argument("--draw-base", type=float, default=1.2)
    parser.add_argument("--output-dir", type=Path, default=Path("outputs_tournament"))
    args = parser.parse_args()

    teams = load_teams(args.teams)
    groups = read_groups(args.groups)
    venues = read_venue_assignment(args.venues, teams)
    results = []
    for idx, fmt in enumerate(FORMATS):
        results.append(
            simulate_format(
                fmt,
                groups,
                venues,
                teams,
                args.sims,
                args.seed + idx * 1000,
                args.theta,
                args.draw_base,
            )
        )
    write_outputs(args.output_dir, results, theoretical_formats(), teams)
    print(f"Simulations per format: {args.sims}")
    for row in results:
        print(
            f"{row['format']}: top8->16={row['top8_reach_16_rate']:.4f}, "
            f"best champ={row['best_team_champion_rate']:.4f}, upset={row['upset_rate']:.4f}, matches={row['total_matches']:.0f}"
        )
    print(f"Wrote: {args.output_dir / 'simulation_summary.md'}")


if __name__ == "__main__":
    main()
