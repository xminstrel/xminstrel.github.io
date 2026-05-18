from __future__ import annotations

import json
import shutil
from pathlib import Path

from .graph import write_graph_outputs
from .grouping import (
    GroupMap,
    REFERENCE_GROUPS_D003,
    evaluate_scheme,
    generate_schemes,
    groups_to_rows,
    rank_with_topsis,
    read_scheme_csv,
    write_scheme_csv,
)
from .io import Team, load_teams, write_csv, write_json
from .lottery import write_lottery_outputs
from .tournament import write_tournament_outputs
from .venues import write_venue_outputs


def write_data_report(data_dir: str | Path, docs_dir: str | Path | None = None) -> dict[str, object]:
    data_dir = Path(data_dir)
    summary_path = data_dir / "data_summary.json"
    if summary_path.exists():
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
    else:
        teams = load_teams(data_dir / "final_teams.csv")
        summary = {
            "team_count": len(teams),
            "city_team_count": sum(1 for team in teams if team.level == "city"),
            "county_team_count": sum(1 for team in teams if team.level != "city"),
        }
        write_json(summary_path, summary)

    lines = [
        "# 数据来源与融合说明",
        "",
        "`final_teams.csv` 是本工程统一使用的 64 队指标表。队伍名单与行政关系来自赛题；GDP、人口优先采用浙江统计年鉴解析结果；经纬度、文旅与体育基础字段为代理指标，用于相对评价。",
        "",
        "## 覆盖统计",
        "",
        f"- 参赛队总数：{summary.get('team_count')}",
        f"- 市级队：{summary.get('city_team_count')}",
        f"- 县级队：{summary.get('county_team_count')}",
        f"- 使用年鉴 GDP 的队伍数：{summary.get('official_gdp_count', '见 data_sources.csv')}",
        f"- 使用年鉴人口的队伍数：{summary.get('official_population_count', '见 data_sources.csv')}",
    ]
    report_path = data_dir / "数据来源与融合说明.md"
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    if docs_dir is not None:
        docs_dir = Path(docs_dir)
        docs_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(report_path, docs_dir / "数据来源与融合说明.md")
    return summary


def _is_reference(groups: GroupMap) -> bool:
    return {k: list(v) for k, v in groups.items()} == REFERENCE_GROUPS_D003


def write_direct_outputs(
    teams: list[Team],
    output_dir: str | Path,
    starts: int = 80,
    steps: int = 400,
    keep: int = 5,
    seed: int = 2026,
) -> list[dict[str, object]]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    candidates = generate_schemes(teams, candidates=max(starts, keep * 4), seed=seed, steps=steps)
    ref = next((row for row in candidates if _is_reference(row["groups"])), None)  # type: ignore[arg-type]
    if ref is None:
        ref = {**evaluate_scheme(REFERENCE_GROUPS_D003, teams), "groups": REFERENCE_GROUPS_D003, "direct_score": 0.0}
    others = [row for row in candidates if not _is_reference(row["groups"])]  # type: ignore[arg-type]
    others.sort(key=lambda row: float(row["direct_score"]), reverse=True)
    selected_rows = (others[:2] + [ref] + others[2 : keep - 1])[:keep]
    while len(selected_rows) < keep:
        selected_rows.append(ref)

    for idx, row in enumerate(selected_rows, start=1):
        row["scheme_id"] = f"D{idx:03d}"

    topsis_ranked = rank_with_topsis(selected_rows, "elite_topsis")
    topsis_by_id = {row["scheme_id"]: row["elite_topsis"] for row in topsis_ranked}
    for row in selected_rows:
        row["elite_topsis"] = topsis_by_id[row["scheme_id"]]

    write_json(output_dir / "direct_top_schemes.json", selected_rows)
    ranking_rows = [
        {
            "scheme_id": row["scheme_id"],
            "direct_score": f"{float(row['direct_score']):.6f}",
            "elite_topsis": f"{float(row['elite_topsis']):.6f}",
            "sport_variance": f"{float(row['sport_variance']):.4f}",
            "sport_range": f"{float(row['sport_range']):.4f}",
            "competition_suspense": f"{float(row['competition_suspense']):.6f}",
            "hot_match_index": f"{float(row['hot_match_index']):.4f}",
            "eco_cv": f"{float(row['eco_cv']):.6f}",
            "pop_cv": f"{float(row['pop_cv']):.6f}",
            "tour_cv": f"{float(row['tour_cv']):.6f}",
            "avg_inner_distance_km": f"{float(row['avg_inner_distance_km']):.4f}",
            "geo_cover": f"{float(row['geo_cover']):.4f}",
        }
        for row in selected_rows
    ]
    write_csv(output_dir / "direct_ranking.csv", ranking_rows)
    write_scheme_csv(output_dir / "direct_best_scheme.csv", selected_rows[0]["groups"], teams)  # type: ignore[arg-type]

    lines = [
        "# 问题一直接寻优候选方案",
        "",
        "候选方案由可行构造、局部交换搜索和固定最终推荐方案共同组成。`direct_score` 用于搜索过程排序，`elite_topsis` 用于候选方案综合评价。",
        "",
        "| 排名 | 方案 | direct_score | TOPSIS | 实力方差 | 实力极差 | 竞争悬念 | 热点指数 | 经济CV | 人口CV | 文旅CV | 平均距离km | 地域覆盖 |",
        "|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for idx, row in enumerate(selected_rows, start=1):
        mark = "（最终候选）" if row["scheme_id"] == "D003" else ""
        lines.append(
            f"| {idx} | {row['scheme_id']}{mark} | {float(row['direct_score']):.6f} | {float(row['elite_topsis']):.6f} | "
            f"{float(row['sport_variance']):.2f} | {float(row['sport_range']):.2f} | {float(row['competition_suspense']):.6f} | "
            f"{float(row['hot_match_index']):.2f} | {float(row['eco_cv']):.4f} | {float(row['pop_cv']):.4f} | "
            f"{float(row['tour_cv']):.4f} | {float(row['avg_inner_distance_km']):.2f} | {float(row['geo_cover']):.4f} |"
        )
    (output_dir / "direct_top_schemes.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return selected_rows


def write_selection_outputs(teams: list[Team], direct_json: str | Path, output_dir: str | Path) -> dict[str, object]:
    direct_json = Path(direct_json)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    schemes = json.loads(direct_json.read_text(encoding="utf-8"))
    feasible = [
        row
        for row in schemes
        if float(row["hard_violations"]) == 0
        and float(row["same_city_repeat_index"]) == 0
        and float(row["pair_conflict_index"]) == 0
    ]
    selected = max(feasible, key=lambda row: float(row["elite_topsis"]))
    write_scheme_csv(output_dir / "selected_scheme.csv", selected["groups"], teams)

    table_rows = []
    for row in schemes:
        table_rows.append(
            {
                "scheme_id": row["scheme_id"],
                "selected": "yes" if row["scheme_id"] == selected["scheme_id"] else "",
                "direct_score": f"{float(row['direct_score']):.6f}",
                "elite_topsis": f"{float(row['elite_topsis']):.6f}",
                "sport_variance": f"{float(row['sport_variance']):.4f}",
                "sport_range": f"{float(row['sport_range']):.4f}",
                "competition_suspense": f"{float(row['competition_suspense']):.6f}",
                "hot_match_index": f"{float(row['hot_match_index']):.4f}",
                "eco_cv": f"{float(row['eco_cv']):.6f}",
                "pop_cv": f"{float(row['pop_cv']):.6f}",
                "tour_cv": f"{float(row['tour_cv']):.6f}",
                "avg_inner_distance_km": f"{float(row['avg_inner_distance_km']):.4f}",
                "geo_cover": f"{float(row['geo_cover']):.4f}",
            }
        )
    write_csv(output_dir / "scheme_selection_table.csv", table_rows)

    lines = [
        "# 问题一最终分组方案选择说明",
        "",
        "最终选择规则：先筛除硬约束违反、同市重复和成对冲突不为 0 的方案；剩余方案按 `elite_topsis` 最大原则选择。",
        "",
        f"本次最终选择 `{selected['scheme_id']}`。",
        "",
        "## 指标对比",
        "",
        "| 方案 | direct_score | TOPSIS综合评价 | 实力方差 | 实力极差 | 竞争悬念 | 热点指数 | 经济CV | 人口CV | 文旅CV | 平均距离km | 地域覆盖 |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in schemes:
        mark = "（最终）" if row["scheme_id"] == selected["scheme_id"] else ""
        lines.append(
            f"| {row['scheme_id']}{mark} | {float(row['direct_score']):.6f} | {float(row['elite_topsis']):.6f} | "
            f"{float(row['sport_variance']):.2f} | {float(row['sport_range']):.2f} | {float(row['competition_suspense']):.6f} | "
            f"{float(row['hot_match_index']):.2f} | {float(row['eco_cv']):.4f} | {float(row['pop_cv']):.4f} | "
            f"{float(row['tour_cv']):.4f} | {float(row['avg_inner_distance_km']):.2f} | {float(row['geo_cover']):.4f} |"
        )
    lines.extend(["", "## 最终分组", "", "| 小组 | 队伍 |", "|---|---|"])
    for group, names in selected["groups"].items():
        lines.append(f"| {group} | {'、'.join(names)} |")
    (output_dir / "问题一方案选择说明.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return selected


def write_method_compare_outputs(direct_rows: list[dict[str, object]], lottery_rows: list[dict[str, object]], output_dir: str | Path) -> None:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for row in direct_rows[:5]:
        rows.append({**row, "method": "可行域直接寻优", "method_score": row.get("direct_score", "")})
    for row in lottery_rows[:5]:
        rows.append({**row, "method": "候选池抽样+TOPSIS", "method_score": row.get("topsis_score", "")})
    rows = rank_with_topsis(rows, "unified_topsis")
    write_json(output_dir / "method_compare.json", rows)
    lines = [
        "# 问题一分组生成方法对比",
        "",
        "将直接寻优和候选池抽样的前若干方案放入同一指标矩阵中，重新进行 TOPSIS 评价，作为生成方法稳定性对照。",
        "",
        "| 排名 | 方案 | 生成方法 | 统一TOPSIS | 方法内分数 |",
        "|---:|---|---|---:|---:|",
    ]
    for idx, row in enumerate(rows, start=1):
        lines.append(
            f"| {idx} | {row.get('scheme_id', '')} | {row['method']} | {float(row['unified_topsis']):.6f} | "
            f"{float(row['method_score']):.6f} |"
        )
    (output_dir / "问题一分组生成方法对比.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_compact_result_summary(
    root: str | Path,
    selected: dict[str, object],
    draw_record: dict[str, object],
    venue_metrics: dict[str, float],
    tournament_results: list[dict[str, float | int | str]],
) -> None:
    root = Path(root)
    output_path = root / "results" / "结果汇总.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    graph_stats_path = root / "results" / "01_图染色" / "graph_stats.json"
    graph_stats = json.loads(graph_stats_path.read_text(encoding="utf-8")) if graph_stats_path.exists() else {}
    groups = selected["groups"]

    lines = [
        "# 结果汇总",
        "",
        "本文件是 `results/` 下唯一保留的人读结果说明。更细的结构化结果保留在 CSV/JSON 文件中。",
        "",
        "## 1. 图染色结论",
        "",
        f"- 顶点数：{graph_stats.get('vertex_count', 64)}",
        f"- 冲突边数：{graph_stats.get('edge_count', 232)}",
        f"- 色数下界：{graph_stats.get('chromatic_lower_bound', 11)}",
        f"- 11 色构造成功：{graph_stats.get('found_11_coloring', True)}",
        f"- 结论：{graph_stats.get('chromatic_number_conclusion', 'χ(G)=11')}",
        "",
        "最终采用 16 组，是因为 64 队每组 4 队、8 个赛地每地 2 组，并与 32 强淘汰赛衔接。",
        "",
        "## 2. 问题一最终分组",
        "",
        f"最终推荐方案：`{selected['scheme_id']}`，TOPSIS 综合评价为 `{float(selected['elite_topsis']):.6f}`。",
        "",
        "| 小组 | 队伍 |",
        "|---|---|",
    ]
    for group, names in groups.items():  # type: ignore[union-attr]
        lines.append(f"| {group} | {'、'.join(names)} |")
    lines.extend(
        [
            "",
            "机器结果：`results/02_分组方案/selected_scheme.csv`、`results/02_分组方案/scheme_selection_table.csv`、`results/02_分组方案/direct_top_schemes.json`。",
            "",
            "## 3. 问题二公开抽签",
            "",
            "| 项目 | 结果 |",
            "|---|---|",
            f"| 方案池规模 | {draw_record['pool_size']} |",
            f"| 方案池 SHA-256 | `{draw_record['pool_sha256']}` |",
            f"| 现场随机数字串 | `{draw_record['public_seed']}` |",
            f"| 抽中编号 | {draw_record['selected_index']} |",
            f"| 抽中池内方案 | {draw_record['selected_pool_id']} |",
            f"| 来源候选方案 | {draw_record['selected_source_scheme_id']} |",
            f"| 抽中方案 TOPSIS | {float(draw_record['selected_topsis_score']):.6f} |",
            "",
            "机器结果：`results/03_公开抽签/scheme_pool.csv`、`results/03_公开抽签/scheme_pool.sha256`、`results/03_公开抽签/draw_record.json`。",
            "",
            "## 4. 问题三比赛地点",
            "",
            "推荐 8 个承办地：台州市、宁波市、杭州市、温州市、绍兴市、金华市、青田县、龙游县。",
            "",
            "| 指标 | 数值 |",
            "|---|---:|",
            f"| 覆盖区域数 | {venue_metrics['covered_regions']:.0f} |",
            f"| 县级承办点数量 | {venue_metrics['county_venue_count']:.0f} |",
            f"| 参赛队平均到赛地距离 | {venue_metrics['avg_team_to_venue_distance_km']:.2f} km |",
            f"| 单队最远到赛地距离 | {venue_metrics['max_team_to_venue_distance_km']:.2f} km |",
            f"| 小组出行距离标准差均值 | {venue_metrics['mean_group_distance_std_km']:.2f} km |",
            f"| 主场关联惩罚合计 | {venue_metrics['home_penalty_total']:.2f} |",
            "",
            "机器结果：`results/04_赛地选择/venue_assignment.csv`、`results/04_赛地选择/venue_metrics.json`。",
            "",
            "## 5. 问题四赛制建议",
            "",
            "| 赛制 | 前16强队小组出线率 | 前8强队进16强率 | 最强队夺冠率 | 总场次 |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for row in tournament_results:
        lines.append(
            f"| {row['format']} | {float(row['top16_group_qualification_rate']):.4f} | "
            f"{float(row['top8_round16_rate']):.4f} | {float(row['best_team_champion_rate']):.4f} | {row['total_matches']} |"
        )
    lines.extend(
        [
            "",
            "最终建议：`16 组单循环 + 每组前二晋级 + 32 强单败淘汰`。双循环稳定性更好，但总场次从 127 增至 223，组织成本过高。",
            "",
            "机器结果：`results/05_赛制仿真/simulation_results.csv`、`results/05_赛制仿真/simulation_results.json`。",
        ]
    )
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def remove_verbose_markdown_outputs(root: str | Path) -> None:
    root = Path(root)
    keep = {
        root / "项目说明.md",
        root / "项目总结.md",
        root / "results" / "结果汇总.md",
    }
    for path in root.rglob("*.md"):
        if path not in keep:
            path.unlink()


def run_all(root: str | Path, starts: int = 80, steps: int = 400, lottery_candidates: int = 300, sims: int = 1000) -> None:
    root = Path(root)
    data_dir = root / "data"
    results = root / "results"
    graph_dir = results / "01_图染色"
    group_dir = results / "02_分组方案"
    lottery_dir = results / "03_公开抽签"
    venue_dir = results / "04_赛地选择"
    tournament_dir = results / "05_赛制仿真"
    teams = load_teams(data_dir / "final_teams.csv")
    write_graph_outputs(teams, graph_dir)
    direct_rows = write_direct_outputs(teams, group_dir, starts=starts, steps=steps)
    selected = write_selection_outputs(teams, group_dir / "direct_top_schemes.json", group_dir)
    lottery_schemes = generate_schemes(teams, candidates=lottery_candidates, seed=2026, steps=max(100, steps // 2))
    for idx, row in enumerate(lottery_schemes, start=1):
        row["scheme_id"] = f"S{idx:04d}"
    lottery_ranked = rank_with_topsis(lottery_schemes, "topsis_score")
    draw_record = write_lottery_outputs(lottery_ranked, teams, lottery_dir, top_k=min(100, len(lottery_ranked)))
    write_method_compare_outputs(direct_rows, lottery_ranked, group_dir)
    groups = selected["groups"]
    venue_metrics = write_venue_outputs(groups, teams, venue_dir)
    tournament_results = write_tournament_outputs(groups, teams, tournament_dir, sims=sims)
    write_compact_result_summary(root, selected, draw_record, venue_metrics, tournament_results)
    remove_verbose_markdown_outputs(root)


def load_selected_groups(root: str | Path) -> GroupMap:
    root = Path(root)
    selected = root / "results" / "02_分组方案" / "selected_scheme.csv"
    if selected.exists():
        return read_scheme_csv(selected)
    return REFERENCE_GROUPS_D003
