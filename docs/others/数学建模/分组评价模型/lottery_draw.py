#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Public lottery mechanism for problem 2.

The script builds a high-quality feasible scheme pool, freezes it with a
SHA-256 hash, and selects one scheme by a public random integer:

    q = (R mod K) + 1

where K is the number of schemes in the frozen pool.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import secrets
from pathlib import Path
from typing import Dict, List, Sequence

from group_evaluator import (
    GROUP_NAMES,
    METRIC_DIRECTIONS,
    combined_weights,
    evaluate_scheme,
    generate_candidate_schemes,
    load_teams,
    positive_normalize,
    scheme_to_named,
    topsis_scores,
    write_scheme_csv,
)


def build_ranked_rows(teams, candidates: int, seed: int, alpha: float) -> tuple[list[dict], dict]:
    schemes = generate_candidate_schemes(
        teams=teams,
        count=candidates,
        seed=seed,
        strict_no_same_city=True,
    )
    if not schemes:
        raise RuntimeError("No feasible schemes generated.")

    rows = []
    for idx, scheme in enumerate(schemes, start=1):
        row = evaluate_scheme(scheme, teams)
        row["source_scheme_id"] = f"S{idx:04d}"
        row["groups"] = scheme
        rows.append(row)

    rows = [row for row in rows if row["hard_violations"] == 0]
    if not rows:
        raise RuntimeError("No legal schemes after hard-constraint check.")

    metrics = list(METRIC_DIRECTIONS.keys())
    z_rows = positive_normalize(rows, metrics)
    weights = combined_weights(z_rows, metrics, alpha=alpha)
    scores = topsis_scores(z_rows, metrics, weights)
    for row, score in zip(rows, scores):
        row["topsis_score"] = score
    rows.sort(key=lambda r: r["topsis_score"], reverse=True)
    return rows, weights


def select_quality_pool(rows: Sequence[dict], top_k: int | None, top_ratio: float) -> list[dict]:
    if top_k is not None:
        k = min(top_k, len(rows))
    else:
        k = max(1, round(len(rows) * top_ratio))
    pool = []
    for idx, row in enumerate(rows[:k], start=1):
        item = dict(row)
        item["pool_id"] = f"P{idx:04d}"
        pool.append(item)
    return pool


def row_for_csv(item: dict, teams) -> dict:
    group_map = scheme_to_named(item["groups"], teams)
    row = {
        "pool_id": item["pool_id"],
        "source_scheme_id": item["source_scheme_id"],
        "topsis_score": f"{item['topsis_score']:.12f}",
    }
    for metric in ["hard_violations", *METRIC_DIRECTIONS.keys()]:
        value = item[metric]
        if isinstance(value, float):
            row[metric] = f"{value:.12f}"
        else:
            row[metric] = value
    for group_name in GROUP_NAMES:
        row[group_name] = "、".join(group_map[group_name])
    return row


def write_pool_files(output_dir: Path, pool: Sequence[dict], teams, weights: dict, args: argparse.Namespace) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "scheme_pool.csv"
    json_path = output_dir / "scheme_pool.json"
    hash_path = output_dir / "scheme_pool.sha256"
    meta_path = output_dir / "pool_metadata.json"

    fieldnames = [
        "pool_id",
        "source_scheme_id",
        "topsis_score",
        "hard_violations",
        *METRIC_DIRECTIONS.keys(),
        *GROUP_NAMES,
    ]
    with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for item in pool:
            writer.writerow(row_for_csv(item, teams))

    serializable = []
    for item in pool:
        row = {key: value for key, value in item.items() if key != "groups"}
        row["groups"] = scheme_to_named(item["groups"], teams)
        serializable.append(row)
    json_path.write_text(json.dumps(serializable, ensure_ascii=False, indent=2), encoding="utf-8")

    digest = hashlib.sha256(csv_path.read_bytes()).hexdigest()
    hash_path.write_text(f"{digest}  {csv_path.name}\n", encoding="utf-8")

    metadata = {
        "method": "优质方案池公开随机抽签法",
        "candidate_count": args.candidates,
        "pool_size": len(pool),
        "seed": args.seed,
        "alpha": args.alpha,
        "top_k": args.top_k,
        "top_ratio": args.top_ratio,
        "strict_no_same_city_counties": True,
        "pool_csv": str(csv_path),
        "pool_sha256": digest,
        "weights": weights,
        "draw_rule": "R = int(SHA256(s | H), 16); q = (R mod K) + 1。s为现场公开数字串，H为方案池SHA-256。",
    }
    meta_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    return metadata


def make_public_random_number(public_seed: str | None, pool_sha256: str, direct_number: int | None) -> tuple[int, str]:
    if public_seed:
        text = f"{public_seed}|{pool_sha256}"
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        return int(digest, 16), f"SHA256({public_seed}|{pool_sha256})={digest}"
    if direct_number is not None:
        return direct_number, "direct_public_integer"
    generated = str(secrets.randbelow(10**16)).zfill(16)
    text = f"{generated}|{pool_sha256}"
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return int(digest, 16), f"generated_seed={generated}; SHA256({generated}|{pool_sha256})={digest}"


def draw_scheme(pool: Sequence[dict], public_number: int) -> tuple[dict, int]:
    if not pool:
        raise ValueError("empty pool")
    k = len(pool)
    q = public_number % k + 1
    return pool[q - 1], q


def write_draw_files(
    output_dir: Path,
    pool: Sequence[dict],
    selected: dict,
    public_seed: str | None,
    public_number: int,
    random_source: str,
    q: int,
    teams,
    metadata: dict,
) -> None:
    md_path = output_dir / "final_draw_scheme.md"
    csv_path = output_dir / "final_draw_scheme.csv"
    record_path = output_dir / "draw_record.json"

    group_map = scheme_to_named(selected["groups"], teams)
    lines = [
        "# 问题二公开抽签结果",
        "",
        "## 抽签规则",
        "",
        f"优质方案池规模：`K={len(pool)}`",
        f"现场公开数字串：`{public_seed if public_seed else '未指定，程序生成'}`",
        f"随机数生成记录：`{random_source}`",
        f"公开随机整数：`R={public_number}`",
        "",
        "$$",
        "R=\\operatorname{int}(\\operatorname{SHA256}(s\\Vert H),16)",
        "$$",
        "",
        "$$",
        "q=(R\\bmod K)+1",
        "$$",
        "",
        f"计算得到：`q={q}`",
        f"抽中方案编号：`{selected['pool_id']}`",
        f"来源候选方案：`{selected['source_scheme_id']}`",
        f"TOPSIS 得分：`{selected['topsis_score']:.6f}`",
        "",
        "## 方案池冻结信息",
        "",
        f"方案池文件：`scheme_pool.csv`",
        f"SHA-256：`{metadata['pool_sha256']}`",
        "",
        "## 最终分组方案",
        "",
        "| 小组 | 队伍 |",
        "|---|---|",
    ]
    for group_name in GROUP_NAMES:
        lines.append(f"| {group_name} | {'、'.join(group_map[group_name])} |")
    lines.extend(["", "## 指标值", "", "| 指标 | 数值 |", "|---|---:|"])
    for metric in ["hard_violations", *METRIC_DIRECTIONS.keys(), "topsis_score"]:
        value = selected[metric]
        if isinstance(value, float):
            lines.append(f"| {metric} | {value:.6f} |")
        else:
            lines.append(f"| {metric} | {value} |")
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    write_scheme_csv(csv_path, selected["groups"], teams)

    record = {
        "public_random_number": public_number,
        "public_seed": public_seed,
        "random_source": random_source,
        "pool_size": len(pool),
        "selected_index": q,
        "selected_pool_id": selected["pool_id"],
        "selected_source_scheme_id": selected["source_scheme_id"],
        "selected_topsis_score": selected["topsis_score"],
        "pool_sha256": metadata["pool_sha256"],
        "draw_rule": "R = int(SHA256(s | H), 16); q = (R mod K) + 1",
    }
    record_path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")


def write_process_doc(output_dir: Path, metadata: dict) -> None:
    path = output_dir / "lottery_process.md"
    lines = [
        "# 问题二抽签过程设计",
        "",
        "本文采用“优质方案池公开随机抽签法”。该方法不是逐队无约束抽签，而是先生成满足全部约束的优质完整分组方案池，再通过公开随机数抽取最终方案。",
        "",
        "## 流程",
        "",
        "1. 利用问题一的约束模型生成候选方案池。",
        "2. 对每个候选方案进行硬约束检验，保留合法方案。",
        "3. 计算行政公平性、竞技公平性、观赏性、经济人口文旅均衡性和地理合理性指标。",
        "4. 使用 AHP-熵权组合赋权和 TOPSIS 得到综合得分。",
        "5. 取综合得分排名前列方案构成优质方案池。",
        "6. 将优质方案池按 `P0001, P0002, ...` 编号并保存为 `scheme_pool.csv`。",
        "7. 计算并公开 `scheme_pool.csv` 的 SHA-256 哈希。",
        "8. 现场抽取数字球或采用其他公开方式得到数字串 `s`。",
        "9. 将数字串 `s` 与已公开的方案池哈希 `H` 拼接，计算随机整数：",
        "",
        "$$",
        "R=\\operatorname{int}(\\operatorname{SHA256}(s\\Vert H),16)",
        "$$",
        "",
        "10. 若方案池规模为 `K`，则计算：",
        "",
        "$$",
        "q=(R\\bmod K)+1",
        "$$",
        "",
        "11. 选取按编号排序后的第 `q` 个方案作为最终分组。",
        "",
        "## 合法性",
        "",
        "优质方案池中的每个方案均满足：",
        "",
        "$$",
        "\\sum_{t\\in T}x_{tg}=4,\\quad \\forall g\\in G",
        "$$",
        "",
        "$$",
        "\\sum_{g=1}^{16}x_{tg}=1,\\quad \\forall t\\in T",
        "$$",
        "",
        "$$",
        "\\sum_{t\\in M}x_{tg}\\leq1,\\quad \\forall g\\in G",
        "$$",
        "",
        "$$",
        "x_{m_i g}+x_{cg}\\leq1,\\quad \\forall i,\\forall c\\in C_i,\\forall g\\in G",
        "$$",
        "",
        "并采用强化条件：",
        "",
        "$$",
        "n_{ig}\\leq1,\\quad \\forall i,g",
        "$$",
        "",
        "因此从方案池中抽出的任意方案都必然满足题目要求。",
        "",
        "## 公平性与透明性",
        "",
        "方案池在抽签前公开并用 SHA-256 哈希冻结，抽签规则提前公开，数字串现场生成，并与方案池哈希绑定后再二次哈希。若公开数字串近似随机，则优质方案池中每个方案被抽中的概率近似相同：",
        "",
        "$$",
        "P(X_k)=\\frac{1}{K},\\quad X_k\\in\\Omega^*",
        "$$",
        "",
        "## 本次运行参数",
        "",
        f"- 候选方案数：`{metadata['candidate_count']}`",
        f"- 优质方案池规模：`{metadata['pool_size']}`",
        f"- 随机种子：`{metadata['seed']}`",
        f"- AHP-熵权组合参数 alpha：`{metadata['alpha']}`",
        f"- 方案池 SHA-256：`{metadata['pool_sha256']}`",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a high-quality scheme pool and draw one final scheme.")
    parser.add_argument("--teams", type=Path, default=Path("data/teams.csv"))
    parser.add_argument("--candidates", type=int, default=2000, help="number of feasible candidate schemes to generate")
    parser.add_argument("--top-k", type=int, default=100, help="pool size; overrides --top-ratio")
    parser.add_argument("--top-ratio", type=float, default=0.2, help="pool ratio if --top-k is omitted")
    parser.add_argument("--seed", type=int, default=2026, help="seed for candidate generation")
    parser.add_argument("--alpha", type=float, default=0.5, help="AHP share in AHP-entropy weights")
    parser.add_argument("--draw-seed", type=str, default=None, help="public digit string, e.g. balls drawn on site")
    parser.add_argument("--draw-number", type=int, default=None, help="legacy direct public integer; used only if --draw-seed is omitted")
    parser.add_argument("--output-dir", type=Path, default=Path("outputs_lottery"))
    args = parser.parse_args()

    teams = load_teams(args.teams)
    rows, weights = build_ranked_rows(teams, candidates=args.candidates, seed=args.seed, alpha=args.alpha)
    pool = select_quality_pool(rows, top_k=args.top_k, top_ratio=args.top_ratio)
    metadata = write_pool_files(args.output_dir, pool, teams, weights, args)
    public_number, random_source = make_public_random_number(args.draw_seed, metadata["pool_sha256"], args.draw_number)
    selected, q = draw_scheme(pool, public_number)
    write_draw_files(args.output_dir, pool, selected, args.draw_seed, public_number, random_source, q, teams, metadata)
    write_process_doc(args.output_dir, metadata)

    print(f"Candidate schemes: {len(rows)}")
    print(f"Quality pool size: {len(pool)}")
    print(f"Pool SHA-256: {metadata['pool_sha256']}")
    print(f"Public random number: {public_number}")
    print(f"Selected index: {q}")
    print(f"Selected pool id: {selected['pool_id']}")
    print(f"Wrote: {args.output_dir / 'scheme_pool.csv'}")
    print(f"Wrote: {args.output_dir / 'final_draw_scheme.md'}")


if __name__ == "__main__":
    main()
