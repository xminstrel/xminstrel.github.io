#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build the Numod3 data layer and conflict-graph analysis.

Data sources:
- teams_from_problem.csv from 数模1: official team list extracted from the problem.
- Zhejiang Statistical Yearbook processed tables from 数模1: GDP and population.
- 分组评价模型/data/teams.csv: existing coordinates, regions, tourism and football proxy fields.

The output data keeps official problem-team membership as the master list and
replaces GDP/population with yearbook values where exact county/city rows exist.
"""

from __future__ import annotations

import csv
import json
import math
import sys
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


ROOT = Path(__file__).resolve().parents[1]
NUMOD3 = ROOT / "数模3"
MODEL_DIR = ROOT / "分组评价模型"
DATA_DIR = NUMOD3 / "data"
GRAPH_DIR = NUMOD3 / "outputs_graph"

sys.path.insert(0, str(MODEL_DIR))
from group_evaluator import Team, load_teams, normalize_by_team, stable_factor  # noqa: E402


TEAM_SOURCE = ROOT / "数模1" / "math_model" / "data" / "raw" / "teams_from_problem.csv"
YEARBOOK_1725 = ROOT / "数模1" / "math_model" / "data" / "processed" / "yearbook" / "17-25.csv"
YEARBOOK_1726 = ROOT / "数模1" / "math_model" / "data" / "processed" / "yearbook" / "17-26.csv"
PROXY_TEAMS = MODEL_DIR / "data" / "teams.csv"


def read_csv_dict(path: Path) -> List[dict]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def to_float(value: str | None) -> float | None:
    if value is None:
        return None
    text = str(value).strip().replace(",", "")
    if text in {"", "—", "--", "nan", "None"}:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def first_existing(row: dict, keywords: Iterable[str]) -> float | None:
    for key, value in row.items():
        if all(k in key for k in keywords):
            num = to_float(value)
            if num is not None:
                return num
    return None


def load_yearbook() -> Tuple[Dict[str, dict], Dict[str, dict]]:
    rows25 = {row["市县名称"].strip(): row for row in read_csv_dict(YEARBOOK_1725)}
    rows26 = {row["市县名称"].strip(): row for row in read_csv_dict(YEARBOOK_1726)}
    return rows25, rows26


def build_enriched_teams() -> Tuple[List[Team], List[dict], dict]:
    problem_rows = read_csv_dict(TEAM_SOURCE)
    proxy_by_name = {t.name: t for t in load_teams(PROXY_TEAMS)}
    y25, y26 = load_yearbook()

    teams: List[Team] = []
    source_rows: List[dict] = []
    missing_gdp: List[str] = []
    missing_pop: List[str] = []

    for idx, row in enumerate(problem_rows, start=1):
        name = row["team"].strip()
        proxy = proxy_by_name[name]
        econ = y25.get(name)
        poprow = y26.get(name)

        gdp = first_existing(econ, ["生产总值"]) if econ else None
        pop = to_float(poprow.get("常住人口")) if poprow else None
        if pop is None and econ:
            pop = first_existing(econ, ["常住人口"])

        gdp_source = "浙江统计年鉴2024表17-25" if gdp is not None else "原模型代理值"
        pop_source = "浙江统计年鉴2024表17-26" if pop is not None else "原模型代理值"

        if gdp is None:
            gdp = proxy.gdp
            missing_gdp.append(name)
        if pop is None:
            pop = proxy.population
            missing_pop.append(name)

        # Tourism and football variables do not have complete official county rows.
        # Re-scale the proxy fields with official GDP/population so the strength
        # indicator reacts to yearbook data while retaining the original model shape.
        football_facility = 0.45 * math.sqrt(max(gdp, 0.0)) + stable_factor(name + "f", 12, 34)
        youth_football = 0.12 * math.sqrt(max(pop, 0.0)) + stable_factor(name + "y", 12, 34)
        sports_investment = 0.35 * math.sqrt(max(gdp, 0.0)) + stable_factor(name + "i", 10, 30)

        quality_parts = []
        quality_parts.append("official_gdp" if name not in missing_gdp else "proxy_gdp")
        quality_parts.append("official_population" if name not in missing_pop else "proxy_population")
        quality_parts.append("proxy_coord_tourism_sports")

        teams.append(
            Team(
                team_id=f"T{idx:02d}",
                name=name,
                level=row["team_level"].strip(),
                parent_city=row["parent_city"].strip(),
                region=proxy.region,
                lon=proxy.lon,
                lat=proxy.lat,
                gdp=float(gdp),
                population=float(pop),
                tourism=proxy.tourism,
                football_facility=football_facility,
                youth_football=youth_football,
                sports_investment=sports_investment,
                data_quality="+".join(quality_parts),
            )
        )
        source_rows.append(
            {
                "team_id": f"T{idx:02d}",
                "name": name,
                "team_level": row["team_level"].strip(),
                "parent_city": row["parent_city"].strip(),
                "admin_type": row["admin_type"].strip(),
                "gdp_source": gdp_source,
                "population_source": pop_source,
                "coordinate_source": "分组评价模型坐标代理",
                "tourism_sports_source": "原模型代理变量",
            }
        )

    summary = {
        "team_count": len(teams),
        "city_team_count": sum(1 for t in teams if t.level == "city"),
        "county_team_count": sum(1 for t in teams if t.level == "county"),
        "official_gdp_count": len(teams) - len(missing_gdp),
        "official_population_count": len(teams) - len(missing_pop),
        "missing_gdp": missing_gdp,
        "missing_population": missing_pop,
    }
    return teams, source_rows, summary


def write_teams(teams: List[Team], source_rows: List[dict], summary: dict) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with (DATA_DIR / "final_teams.csv").open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(teams[0].__dict__.keys()))
        writer.writeheader()
        for team in teams:
            writer.writerow(team.__dict__)

    with (DATA_DIR / "data_sources.csv").open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(source_rows[0].keys()))
        writer.writeheader()
        writer.writerows(source_rows)

    (DATA_DIR / "data_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")


def build_edges(teams: List[Team]) -> set[Tuple[str, str]]:
    edges: set[Tuple[str, str]] = set()
    cities = [t for t in teams if t.level == "city"]

    # City-level teams must be in different groups: complete graph K11.
    for i in range(len(cities)):
        for j in range(i + 1, len(cities)):
            a, b = sorted([cities[i].team_id, cities[j].team_id])
            edges.add((a, b))

    # Strengthened administrative avoidance used by the final optimization:
    # each parent-city administrative system appears at most once in a group.
    by_parent: Dict[str, List[Team]] = {}
    for team in teams:
        by_parent.setdefault(team.parent_city, []).append(team)
    for members in by_parent.values():
        for i in range(len(members)):
            for j in range(i + 1, len(members)):
                a, b = sorted([members[i].team_id, members[j].team_id])
                edges.add((a, b))
    return edges


def clique_stats(teams: List[Team], edges: set[Tuple[str, str]]) -> dict:
    city_ids = [t.team_id for t in teams if t.level == "city"]
    parent_counts = Counter(t.parent_city for t in teams)
    return {
        "city_clique_size": len(city_ids),
        "largest_parent_city_clique_size": max(parent_counts.values()),
        "chromatic_lower_bound": max(len(city_ids), max(parent_counts.values())),
        "edge_count": len(edges),
    }


def greedy_coloring(teams: List[Team], edges: set[Tuple[str, str]], color_count: int) -> Dict[str, int] | None:
    neighbors: Dict[str, set[str]] = {t.team_id: set() for t in teams}
    for a, b in edges:
        neighbors[a].add(b)
        neighbors[b].add(a)

    color: Dict[str, int] = {}
    ids = [t.team_id for t in teams]

    def choose_vertex() -> str:
        uncolored = [v for v in ids if v not in color]
        return max(uncolored, key=lambda v: (len({color[n] for n in neighbors[v] if n in color}), len(neighbors[v])))

    def search() -> bool:
        if len(color) == len(ids):
            return True
        v = choose_vertex()
        used = {color[n] for n in neighbors[v] if n in color}
        for c in range(color_count):
            if c in used:
                continue
            color[v] = c
            if search():
                return True
            del color[v]
        return False

    return color if search() else None


def write_graph_outputs(teams: List[Team], edges: set[Tuple[str, str]], stats: dict) -> None:
    GRAPH_DIR.mkdir(parents=True, exist_ok=True)
    by_id = {t.team_id: t for t in teams}
    color11 = greedy_coloring(teams, edges, 11)
    stats["found_11_coloring"] = color11 is not None
    stats["chromatic_number_conclusion"] = "χ(G)=11" if color11 is not None and stats["chromatic_lower_bound"] == 11 else "需要进一步验证"

    with (GRAPH_DIR / "conflict_edges.csv").open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["team_a_id", "team_a_name", "team_b_id", "team_b_name"])
        for a, b in sorted(edges):
            writer.writerow([a, by_id[a].name, b, by_id[b].name])

    if color11:
        with (GRAPH_DIR / "eleven_color_witness.csv").open("w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["color", "team_id", "team_name", "parent_city", "level"])
            for tid, c in sorted(color11.items(), key=lambda item: (item[1], item[0])):
                team = by_id[tid]
                writer.writerow([c + 1, tid, team.name, team.parent_city, team.level])

    parent_counts = Counter(t.parent_city for t in teams)
    lines = [
        "# 图染色法合法性分析",
        "",
        "## 冲突图定义",
        "",
        "将每支参赛队视为图中的一个顶点。若两支队伍不能分在同一小组，则在两点之间连边。本文采用强化行政回避原则：市级队之间两两冲突；同一地级市行政体系内的市级队和县级队、县级队之间均视为冲突。",
        "",
        "## 图指标",
        "",
        f"- 顶点数：{len(teams)}",
        f"- 边数：{len(edges)}",
        f"- 市级队构成完全图规模：K{stats['city_clique_size']}",
        f"- 最大同行政体系团规模：{stats['largest_parent_city_clique_size']}",
        f"- 色数下界：{stats['chromatic_lower_bound']}",
        f"- 11 色构造是否成功：{'是' if stats['found_11_coloring'] else '否'}",
        f"- 色数结论：{stats['chromatic_number_conclusion']}",
        "",
        "由于 11 支市级队两两不能同组，它们构成完全图 K11，因此冲突图色数至少为 11。程序进一步构造出一个合法 11 色着色，所以在强化行政回避意义下，理论最少小组数为 11。",
        "",
        "但赛题第三问要求 8 个比赛地点、每个地点承办 2 个小组，同时 64 支队伍若采用 16 组可得到每组 4 队的均衡结构。因此最终采用 16 组不是因为冲突图必须 16 色，而是因为赛地容量、赛程衔接和小组规模均衡共同决定。",
        "",
        "## 各行政体系队伍数",
        "",
        "| 行政体系 | 队伍数 |",
        "|---|---:|",
    ]
    for parent, count in sorted(parent_counts.items()):
        lines.append(f"| {parent} | {count} |")
    (GRAPH_DIR / "graph_coloring_analysis.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (GRAPH_DIR / "graph_stats.json").write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")


def write_data_report(summary: dict) -> None:
    lines = [
        "# 数据来源与融合说明",
        "",
        "## 数据表",
        "",
        "- `final_teams.csv`：数模3最终使用的队伍与指标表。",
        "- `data_sources.csv`：每支队伍各字段的数据来源说明。",
        "- `data_summary.json`：数据覆盖统计。",
        "",
        "## 来源说明",
        "",
        "队伍名单、队伍级别、所属或代管地级市来自 `数模1/math_model/data/raw/teams_from_problem.csv`，该文件由赛题 PDF 结构化得到。",
        "",
        "GDP、人口优先使用 `数模1/math_model/data/processed/yearbook/17-25.csv` 和 `17-26.csv`，二者来自浙江统计年鉴 2024 的已解析数据。若年鉴中没有对应的地级市汇总行，则沿用原模型中的市级代理值。",
        "",
        "经纬度、区域、文旅和体育基础变量目前沿用 `分组评价模型/data/teams.csv` 中的代理变量。论文中应明确：这些字段用于构造相对评价指标，不代表真实球队实力或真实场馆承载能力。",
        "",
        "## 覆盖统计",
        "",
        f"- 参赛队总数：{summary['team_count']}",
        f"- 市级队：{summary['city_team_count']}",
        f"- 县级队：{summary['county_team_count']}",
        f"- 使用年鉴 GDP 的队伍数：{summary['official_gdp_count']}",
        f"- 使用年鉴人口的队伍数：{summary['official_population_count']}",
        f"- GDP 缺失而使用代理值的队伍：{'、'.join(summary['missing_gdp']) if summary['missing_gdp'] else '无'}",
        f"- 人口缺失而使用代理值的队伍：{'、'.join(summary['missing_population']) if summary['missing_population'] else '无'}",
    ]
    (DATA_DIR / "数据来源与融合说明.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    teams, source_rows, summary = build_enriched_teams()
    write_teams(teams, source_rows, summary)
    write_data_report(summary)
    edges = build_edges(teams)
    stats = clique_stats(teams, edges)
    write_graph_outputs(teams, edges, stats)
    print(f"Built enriched teams: {len(teams)}")
    print(f"Official GDP rows: {summary['official_gdp_count']}/{summary['team_count']}")
    print(f"Official population rows: {summary['official_population_count']}/{summary['team_count']}")
    print(f"Conflict graph edges: {len(edges)}")
    print(f"Graph conclusion: {stats.get('chromatic_number_conclusion', '')}")


if __name__ == "__main__":
    main()
