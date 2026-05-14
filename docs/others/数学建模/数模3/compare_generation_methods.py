#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Compare grouping-generation methods under a unified TOPSIS matrix."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODEL_DIR = ROOT / "分组评价模型"
NUMOD3 = ROOT / "数模3"

sys.path.insert(0, str(MODEL_DIR))
from group_evaluator import METRIC_DIRECTIONS, combined_weights, positive_normalize, topsis_scores  # noqa: E402


def load_rows(path: Path, method: str, score_key: str, top_n: int = 5) -> list[dict]:
    rows = json.loads(path.read_text(encoding="utf-8"))[:top_n]
    out = []
    for row in rows:
        item = {k: row[k] for k in ["hard_violations", *METRIC_DIRECTIONS.keys()]}
        item["scheme_id"] = row["scheme_id"]
        item["method"] = method
        item["method_score"] = row.get(score_key, row.get("topsis_score", ""))
        item["groups"] = row["groups"]
        out.append(item)
    return out


def main() -> None:
    candidate_rows = load_rows(NUMOD3 / "outputs_candidate_eval" / "candidate_schemes.json", "候选池抽样+TOPSIS", "topsis_score")
    direct_rows = load_rows(NUMOD3 / "outputs_direct" / "direct_top_schemes.json", "可行域直接寻优", "direct_score")
    rows = candidate_rows + direct_rows
    metrics = list(METRIC_DIRECTIONS.keys())
    z_rows = positive_normalize(rows, metrics)
    weights = combined_weights(z_rows, metrics, alpha=0.5)
    scores = topsis_scores(z_rows, metrics, weights)
    for row, score in zip(rows, scores):
        row["unified_topsis"] = score
    rows.sort(key=lambda r: r["unified_topsis"], reverse=True)

    out_dir = NUMOD3 / "outputs_method_compare"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "method_compare.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / "method_compare_weights.json").write_text(json.dumps(weights, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# 问题一分组生成方法对比",
        "",
        "本文对两类可运行方案生成方法进行比较：候选池抽样生成 + TOPSIS 排序、可行域内直接寻优。为避免不同方法内部 TOPSIS 归一化集合不同导致分数不可比，本文取两类方法各自前 5 个方案，共 10 个方案，重新放入同一指标矩阵中进行 AHP-熵权-TOPSIS 评价。",
        "",
        "## 统一评价结果",
        "",
        "| 统一排名 | 方案 | 生成方法 | 统一TOPSIS | 方法内分数 | 实力方差 | 实力极差 | 竞争悬念 | 热点指数 | 经济CV | 人口CV | 文旅CV | 平均距离km | 地域覆盖 |",
        "|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for idx, row in enumerate(rows, start=1):
        mark = "（最终）" if row["scheme_id"] == "D003" else ""
        lines.append(
            f"| {idx} | {row['scheme_id']}{mark} | {row['method']} | {row['unified_topsis']:.6f} | "
            f"{float(row['method_score']):.6f} | {row['sport_variance']:.2f} | {row['sport_range']:.2f} | "
            f"{row['competition_suspense']:.6f} | {row['hot_match_index']:.2f} | {row['eco_cv']:.4f} | "
            f"{row['pop_cv']:.4f} | {row['tour_cv']:.4f} | {row['avg_inner_distance_km']:.2f} | {row['geo_cover']:.4f} |"
        )

    selected = rows[0]
    lines.extend(
        [
            "",
            "## 结论",
            "",
            f"统一评价后排名第一的是 `{selected['scheme_id']}`，生成方法为 `{selected['method']}`，统一 TOPSIS 为 `{selected['unified_topsis']:.6f}`。",
            "",
            "候选池抽样法更容易获得平均距离较小或热点指数较高的方案，但在本次运行中实力方差和实力极差明显偏大；直接寻优法能显著降低实力方差和实力极差，整体更符合公平性优先的评价目标。因此最终分组仍采用直接寻优方案 D003。",
            "",
            "需要说明：该比较是在候选池法前 5 与直接寻优法前 5 的联合集合内进行，不构成全可行域全局最优证明。",
        ]
    )
    (out_dir / "问题一分组生成方法对比.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Best unified scheme: {selected['scheme_id']} {selected['unified_topsis']:.6f}")
    print(out_dir / "问题一分组生成方法对比.md")


if __name__ == "__main__":
    main()
