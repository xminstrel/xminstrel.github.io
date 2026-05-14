from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

from .io import Team


Edge = tuple[str, str]


def build_conflict_edges(teams: list[Team]) -> set[Edge]:
    edges: set[Edge] = set()
    city_teams = [team for team in teams if team.level == "city"]

    for i, team_a in enumerate(city_teams):
        for team_b in city_teams[i + 1 :]:
            edges.add(tuple(sorted((team_a.team_id, team_b.team_id))))

    by_parent: dict[str, list[Team]] = {}
    for team in teams:
        by_parent.setdefault(team.parent_city, []).append(team)

    for members in by_parent.values():
        for i, team_a in enumerate(members):
            for team_b in members[i + 1 :]:
                edges.add(tuple(sorted((team_a.team_id, team_b.team_id))))

    return edges


def color_conflict_graph(teams: list[Team], edges: set[Edge], color_count: int = 11) -> dict[str, int] | None:
    neighbors: dict[str, set[str]] = {team.team_id: set() for team in teams}
    for a, b in edges:
        neighbors[a].add(b)
        neighbors[b].add(a)

    order = [team.team_id for team in teams]
    colors: dict[str, int] = {}

    def choose_vertex() -> str:
        uncolored = [team_id for team_id in order if team_id not in colors]
        return max(
            uncolored,
            key=lambda team_id: (
                len({colors[n] for n in neighbors[team_id] if n in colors}),
                len(neighbors[team_id]),
            ),
        )

    def search() -> bool:
        if len(colors) == len(order):
            return True
        team_id = choose_vertex()
        used = {colors[n] for n in neighbors[team_id] if n in colors}
        for color in range(1, color_count + 1):
            if color in used:
                continue
            colors[team_id] = color
            if search():
                return True
            del colors[team_id]
        return False

    return colors if search() else None


def graph_stats(teams: list[Team], edges: set[Edge], coloring: dict[str, int] | None) -> dict[str, object]:
    parent_counts = Counter(team.parent_city for team in teams)
    city_count = sum(1 for team in teams if team.level == "city")
    lower_bound = max(city_count, max(parent_counts.values()))
    return {
        "vertex_count": len(teams),
        "edge_count": len(edges),
        "city_clique_size": city_count,
        "largest_parent_city_clique_size": max(parent_counts.values()),
        "chromatic_lower_bound": lower_bound,
        "found_11_coloring": coloring is not None,
        "chromatic_number_conclusion": "χ(G)=11" if lower_bound == 11 and coloring else "需要进一步验证",
    }


def write_graph_outputs(teams: list[Team], output_dir: str | Path) -> dict[str, object]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    edges = build_conflict_edges(teams)
    coloring = color_conflict_graph(teams, edges, 11)
    stats = graph_stats(teams, edges, coloring)
    by_id = {team.team_id: team for team in teams}

    with (output_dir / "conflict_edges.csv").open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["team_a_id", "team_a_name", "team_b_id", "team_b_name"])
        for a, b in sorted(edges):
            writer.writerow([a, by_id[a].name, b, by_id[b].name])

    if coloring:
        with (output_dir / "eleven_color_witness.csv").open("w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["color", "team_id", "team_name", "parent_city", "level"])
            for team_id, color in sorted(coloring.items(), key=lambda item: (item[1], item[0])):
                team = by_id[team_id]
                writer.writerow([color, team.team_id, team.name, team.parent_city, team.level])

    parent_counts = Counter(team.parent_city for team in teams)
    lines = [
        "# 图染色法合法性分析",
        "",
        "## 冲突图定义",
        "",
        "将每支参赛队视为图中的一个顶点。若两支队伍不能分在同一小组，则在两点之间连边。本文采用强化行政回避原则：市级队之间两两冲突；同一地级市行政体系内的市级队和县级队、县级队之间均视为冲突。",
        "",
        "## 图指标",
        "",
        f"- 顶点数：{stats['vertex_count']}",
        f"- 边数：{stats['edge_count']}",
        f"- 市级队构成完全图规模：K{stats['city_clique_size']}",
        f"- 最大同行政体系团规模：{stats['largest_parent_city_clique_size']}",
        f"- 色数下界：{stats['chromatic_lower_bound']}",
        f"- 11 色构造是否成功：{'是' if stats['found_11_coloring'] else '否'}",
        f"- 色数结论：{stats['chromatic_number_conclusion']}",
        "",
        "由于 11 支市级队两两不能同组，它们构成完全图 K11，因此冲突图色数至少为 11。程序进一步构造出一个合法 11 色着色，所以在强化行政回避意义下，理论最少小组数为 11。",
        "",
        "最终仍采用 16 组，是因为赛题固定 64 支队、16 个 4 队小组，并要求 8 个赛地每地承办 2 个小组；该数量由赛地容量、小组规模均衡和 32 强淘汰赛衔接共同决定。",
        "",
        "## 各行政体系队伍数",
        "",
        "| 行政体系 | 队伍数 |",
        "|---|---:|",
    ]
    for parent, count in sorted(parent_counts.items()):
        lines.append(f"| {parent} | {count} |")
    (output_dir / "graph_coloring_analysis.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (output_dir / "graph_stats.json").write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
    return stats
