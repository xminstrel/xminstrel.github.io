#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Select the final grouping scheme by explicit evaluation criteria."""

from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NUMOD3 = ROOT / "数模3"
TEAM_PATH = NUMOD3 / "data" / "final_teams.csv"
SCHEME_JSON = NUMOD3 / "outputs_direct" / "direct_top_schemes.json"
OUT_DIR = NUMOD3 / "outputs_selection"


COST_METRICS = {
    "sport_variance": "实力方差",
    "sport_range": "实力极差",
    "eco_cv": "经济CV",
    "pop_cv": "人口CV",
    "tour_cv": "文旅CV",
    "avg_inner_distance_km": "平均距离",
}

BENEFIT_METRICS = {
    "competition_suspense": "竞争悬念",
    "hot_match_index": "热点指数",
    "geo_cover": "地域覆盖",
}


def read_teams() -> dict[str, dict]:
    with TEAM_PATH.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    return {row["name"]: row for row in rows}


def fmt(value: float) -> str:
    return f"{value:.6f}" if abs(value) < 10 else f"{value:.2f}"


def main() -> None:
    schemes = json.loads(SCHEME_JSON.read_text(encoding="utf-8"))
    teams_by_name = read_teams()
    feasible = [
        s
        for s in schemes
        if s["hard_violations"] == 0
        and s["same_city_repeat_index"] == 0
        and s["pair_conflict_index"] == 0
    ]
    selected = max(feasible, key=lambda s: s["elite_topsis"])
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    selected_csv = OUT_DIR / "selected_scheme.csv"
    with selected_csv.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["group", "slot", "team_id", "team_name", "level", "parent_city", "region"])
        for group, names in selected["groups"].items():
            for slot, name in enumerate(names, start=1):
                team = teams_by_name[name]
                writer.writerow([group, slot, team["team_id"], name, team["level"], team["parent_city"], team["region"]])

    with (OUT_DIR / "scheme_selection_table.csv").open("w", encoding="utf-8-sig", newline="") as f:
        fieldnames = [
            "scheme_id",
            "selected",
            "direct_score",
            "elite_topsis",
            "sport_variance",
            "sport_range",
            "competition_suspense",
            "hot_match_index",
            "eco_cv",
            "pop_cv",
            "tour_cv",
            "avg_inner_distance_km",
            "geo_cover",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for s in schemes:
            writer.writerow({k: ("yes" if k == "selected" and s is selected else s.get(k, "")) for k in fieldnames})

    d001 = next(s for s in schemes if s["scheme_id"] == "D001")
    lines = [
        "# 问题一最终分组方案选择说明",
        "",
        "## 评价口径",
        "",
        "本轮直接寻优输出中有两个分数：",
        "",
        "- `direct_score`：模拟退火/局部搜索的直接目标值，用于引导搜索。它把各指标映射为效用后加权求和，适合在搜索过程中快速比较邻域方案。",
        "- `elite_topsis`：对最终保留的优质方案按 AHP-熵权组合权重进行正向化和 TOPSIS 综合评价后的贴近度，适合作为论文中“多指标综合评价”的最终排序依据。",
        "",
        "因此最终选优规则为：先要求硬约束违反数、同市重复指数、成对冲突指数均为 0；在全部合格方案中，以 `elite_topsis` 最大者作为问题一推荐方案。`direct_score` 只作为搜索质量参考，不作为最终唯一决策指标。",
        "",
        f"按此规则，最终选择 `{selected['scheme_id']}`，而不是直接目标值略高的 `D001`。",
        "",
        "## 方案指标对比",
        "",
        "| 方案 | direct_score | TOPSIS综合评价 | 实力方差 | 实力极差 | 竞争悬念 | 热点指数 | 经济CV | 人口CV | 文旅CV | 平均距离km | 地域覆盖 |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for s in schemes:
        mark = "（最终）" if s is selected else ""
        lines.append(
            f"| {s['scheme_id']}{mark} | {s['direct_score']:.6f} | {s['elite_topsis']:.6f} | "
            f"{s['sport_variance']:.2f} | {s['sport_range']:.2f} | {s['competition_suspense']:.6f} | "
            f"{s['hot_match_index']:.2f} | {s['eco_cv']:.4f} | {s['pop_cv']:.4f} | {s['tour_cv']:.4f} | "
            f"{s['avg_inner_distance_km']:.2f} | {s['geo_cover']:.4f} |"
        )

    lines.extend(
        [
            "",
            "## D003 优于 D001 的主要原因",
            "",
            f"- TOPSIS 综合评价：D003 为 {selected['elite_topsis']:.6f}，D001 为 {d001['elite_topsis']:.6f}。",
            f"- 实力方差：D003 为 {selected['sport_variance']:.2f}，低于 D001 的 {d001['sport_variance']:.2f}。",
            f"- 实力极差：D003 为 {selected['sport_range']:.2f}，低于 D001 的 {d001['sport_range']:.2f}。",
            f"- 平均组内距离：D003 为 {selected['avg_inner_distance_km']:.2f} km，低于 D001 的 {d001['avg_inner_distance_km']:.2f} km。",
            f"- 地域覆盖：D003 为 {selected['geo_cover']:.4f}，高于 D001 的 {d001['geo_cover']:.4f}。",
            f"- 热点指数：D003 为 {selected['hot_match_index']:.2f}，高于 D001 的 {d001['hot_match_index']:.2f}。",
            "",
            "D003 的不足是竞争悬念低于 D001，文旅 CV 高于 D001。但在本文评价体系中，行政合法性相同的前提下，实力均衡、地理合理性和综合 TOPSIS 贴近度更能反映整体公平性，因此选择 D003。",
            "",
            "## 最终分组 D003",
            "",
            "| 小组 | 队伍 |",
            "|---|---|",
        ]
    )
    for group, names in selected["groups"].items():
        lines.append(f"| {group} | {'、'.join(names)} |")
    (OUT_DIR / "问题一方案选择说明.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Selected scheme: {selected['scheme_id']}, TOPSIS={selected['elite_topsis']:.6f}")
    print(f"Wrote: {selected_csv}")


if __name__ == "__main__":
    main()
