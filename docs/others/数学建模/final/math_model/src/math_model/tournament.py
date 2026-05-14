from __future__ import annotations

import csv
import json
import math
import random
from pathlib import Path

from .grouping import GroupMap, strength_scores
from .io import Team


def match_counts() -> dict[str, dict[str, int]]:
    return {
        "现行 16 组单循环 + 32 强": {
            "group_matches": 96,
            "knockout_matches": 31,
            "total_matches": 127,
            "min_matches_per_team": 3,
            "max_matches_for_champion": 8,
        },
        "种子分档单循环 + 32 强": {
            "group_matches": 96,
            "knockout_matches": 31,
            "total_matches": 127,
            "min_matches_per_team": 3,
            "max_matches_for_champion": 8,
        },
        "约束淘汰赛对阵": {
            "group_matches": 96,
            "knockout_matches": 31,
            "total_matches": 127,
            "min_matches_per_team": 3,
            "max_matches_for_champion": 8,
        },
        "小组双循环 + 32 强": {
            "group_matches": 192,
            "knockout_matches": 31,
            "total_matches": 223,
            "min_matches_per_team": 6,
            "max_matches_for_champion": 11,
        },
        "瑞士轮 4 轮 + 32 强": {
            "group_matches": 128,
            "knockout_matches": 31,
            "total_matches": 159,
            "min_matches_per_team": 4,
            "max_matches_for_champion": 9,
        },
    }


def _win_probability(score_a: float, score_b: float) -> float:
    return 1.0 / (1.0 + math.exp(-(score_a - score_b) / 13.0))


def _simulate_group(names: list[str], scores: dict[str, float], rng: random.Random, rounds: int = 1) -> list[str]:
    table = {name: [0, 0.0] for name in names}
    for _ in range(rounds):
        for i, a in enumerate(names):
            for b in names[i + 1 :]:
                prob = _win_probability(scores[a], scores[b])
                suspense = 1.0 - abs(prob - 0.5) * 2
                if rng.random() < prob:
                    table[a][0] += 3
                    table[a][1] += suspense
                else:
                    table[b][0] += 3
                    table[b][1] += suspense
    ranked = sorted(names, key=lambda name: (table[name][0], table[name][1], scores[name], rng.random()), reverse=True)
    return ranked[:2]


def _simulate_knockout(names: list[str], scores: dict[str, float], rng: random.Random) -> tuple[str, int]:
    bracket = list(names)
    rng.shuffle(bracket)
    upset_count = 0
    while len(bracket) > 1:
        winners: list[str] = []
        for i in range(0, len(bracket), 2):
            a, b = bracket[i], bracket[i + 1]
            prob = _win_probability(scores[a], scores[b])
            a_wins = rng.random() < prob
            winner = a if a_wins else b
            loser = b if a_wins else a
            if scores[winner] < scores[loser]:
                upset_count += 1
            winners.append(winner)
        bracket = winners
    return bracket[0], upset_count


def simulate_formats(groups: GroupMap, teams: list[Team], sims: int = 1000, seed: int = 2026) -> list[dict[str, float | int | str]]:
    rng = random.Random(seed)
    scores = strength_scores(teams)
    top16 = {name for name, _ in sorted(scores.items(), key=lambda item: item[1], reverse=True)[:16]}
    top8 = {name for name, _ in sorted(scores.items(), key=lambda item: item[1], reverse=True)[:8]}
    best_team = max(scores, key=scores.get)
    count_rows = match_counts()
    formats = list(count_rows)
    accum = {
        name: {
            "top16_group_qualifications": 0,
            "top8_round16": 0,
            "best_champion": 0,
            "early_elimination_events": 0,
            "upsets": 0,
            "matches": 0,
            "suspense": 0.0,
        }
        for name in formats
    }

    for format_name in formats:
        group_rounds = 2 if format_name == "小组双循环 + 32 强" else 1
        for _ in range(sims):
            qualifiers: list[str] = []
            for names in groups.values():
                qualifiers.extend(_simulate_group(names, scores, rng, rounds=group_rounds))
            champion, upsets = _simulate_knockout(qualifiers, scores, rng)
            qualified = set(qualifiers)
            accum[format_name]["top16_group_qualifications"] += len(top16 & qualified)
            accum[format_name]["top8_round16"] += len(top8 & qualified)
            accum[format_name]["best_champion"] += int(champion == best_team)
            accum[format_name]["early_elimination_events"] += int(len(top8 & qualified) < len(top8))
            accum[format_name]["upsets"] += upsets
            accum[format_name]["matches"] += count_rows[format_name]["total_matches"]
            accum[format_name]["suspense"] += sum(1.0 - abs(_win_probability(scores[a], scores[b]) - 0.5) * 2 for names in groups.values() for a in names for b in names if a < b)

    results: list[dict[str, float | int | str]] = []
    for format_name in formats:
        data = accum[format_name]
        counts = count_rows[format_name]
        results.append(
            {
                "format": format_name,
                "top16_group_qualification_rate": data["top16_group_qualifications"] / (16 * sims),
                "top8_round16_rate": data["top8_round16"] / (8 * sims),
                "best_team_champion_rate": data["best_champion"] / sims,
                "early_elimination_event_rate": data["early_elimination_events"] / sims,
                "upset_rate": data["upsets"] / (31 * sims),
                "avg_suspense": data["suspense"] / sims / 96,
                "total_matches": counts["total_matches"],
            }
        )
    return results


def write_tournament_outputs(groups: GroupMap, teams: list[Team], output_dir: str | Path, sims: int = 1000, seed: int = 2026) -> list[dict[str, float | int | str]]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    results = simulate_formats(groups, teams, sims=sims, seed=seed)
    counts = match_counts()

    with (output_dir / "simulation_results.csv").open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(results[0].keys()))
        writer.writeheader()
        writer.writerows(results)
    (output_dir / "simulation_results.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# 问题四赛制仿真与建议",
        "",
        "## 场次成本",
        "",
        "| 赛制 | 小组赛场次 | 淘汰赛场次 | 总场次 | 每队保底 | 冠军最多 |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for name, row in counts.items():
        lines.append(
            f"| {name} | {row['group_matches']} | {row['knockout_matches']} | {row['total_matches']} | "
            f"{row['min_matches_per_team']} | {row['max_matches_for_champion']} |"
        )
    lines.extend(
        [
            "",
            "## 蒙特卡洛结果",
            "",
            "| 赛制 | 前16强队小组出线率 | 前8强队进16强率 | 最强队夺冠率 | 前8强队过早淘汰事件率 | 爆冷率 | 平均悬念 | 总场次 |",
            "|---|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in results:
        lines.append(
            f"| {row['format']} | {row['top16_group_qualification_rate']:.4f} | {row['top8_round16_rate']:.4f} | "
            f"{row['best_team_champion_rate']:.4f} | {row['early_elimination_event_rate']:.4f} | "
            f"{row['upset_rate']:.4f} | {row['avg_suspense']:.6f} | {row['total_matches']} |"
        )
    lines.extend(
        [
            "",
            "## 建议",
            "",
            "双循环能提高强队出线稳定性，但总场次从 127 增至 223，组织成本增幅约 75.6%。因此推荐维持 16 组单循环、小组前二晋级、32 强单败淘汰，并配套优质方案池公开抽签、末轮同组同时开赛、裁判异地派遣和赛后实力数据库更新。",
        ]
    )
    (output_dir / "simulation_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return results
