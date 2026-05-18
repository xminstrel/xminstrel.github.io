from __future__ import annotations

import json
import math
from pathlib import Path

from .grouping import GroupMap, haversine_km
from .io import Team, team_lookup, write_csv


REFERENCE_VENUES_D003: dict[str, str] = {
    "G10": "台州市",
    "G12": "台州市",
    "G02": "宁波市",
    "G09": "宁波市",
    "G06": "杭州市",
    "G15": "杭州市",
    "G07": "温州市",
    "G08": "温州市",
    "G05": "绍兴市",
    "G16": "绍兴市",
    "G03": "金华市",
    "G11": "金华市",
    "G01": "青田县",
    "G13": "青田县",
    "G04": "龙游县",
    "G14": "龙游县",
}


def _std(values: list[float]) -> float:
    mean = sum(values) / len(values)
    return math.sqrt(sum((value - mean) ** 2 for value in values) / len(values))


def assign_reference_venues(groups: GroupMap) -> dict[str, str]:
    missing = set(groups) - set(REFERENCE_VENUES_D003)
    if missing:
        raise ValueError(f"缺少参考赛地分配：{sorted(missing)}")
    return {group: REFERENCE_VENUES_D003[group] for group in groups}


def venue_assignment_rows(groups: GroupMap, teams: list[Team], assignment: dict[str, str]) -> list[dict[str, object]]:
    by_name = team_lookup(teams)
    rows: list[dict[str, object]] = []
    for group in sorted(groups):
        venue = by_name[assignment[group]]
        members = [by_name[name] for name in groups[group]]
        distances = [haversine_km(member, venue) for member in members]
        rows.append(
            {
                "venue": venue.name,
                "region": venue.region,
                "host_groups": group,
                "group_teams": "、".join(groups[group]),
                "avg_distance_km": f"{sum(distances) / len(distances):.2f}",
                "max_distance_km": f"{max(distances):.2f}",
            }
        )
    rows.sort(key=lambda row: (row["venue"], row["host_groups"]))
    return rows


def venue_metrics(groups: GroupMap, teams: list[Team], assignment: dict[str, str]) -> dict[str, float]:
    by_name = team_lookup(teams)
    venue_names = sorted(set(assignment.values()))
    venue_teams = [by_name[name] for name in venue_names]
    all_distances: list[float] = []
    group_stds: list[float] = []
    home_penalty = 0.0
    strong_home_groups = 0

    for group, names in groups.items():
        venue = by_name[assignment[group]]
        distances = [haversine_km(by_name[name], venue) for name in names]
        all_distances.extend(distances)
        group_stds.append(_std(distances))
        if venue.name in names:
            home_penalty += 1.0
            strong_home_groups += 1
        elif any(by_name[name].parent_city == venue.parent_city for name in names):
            home_penalty += 0.25

    region_counts: dict[str, int] = {}
    for venue in venue_teams:
        region_counts[venue.region] = region_counts.get(venue.region, 0) + 1
    ideal = len(venue_teams) / max(len(region_counts), 1)
    region_penalty = sum(abs(count - ideal) for count in region_counts.values()) / len(venue_teams)
    propagation = sum(math.log1p(team.population) + 0.2 * math.log1p(team.tourism) for team in venue_teams) / len(venue_teams)

    return {
        "covered_regions": float(len(region_counts)),
        "county_venue_count": float(sum(1 for team in venue_teams if team.level != "city")),
        "avg_team_to_venue_distance_km": sum(all_distances) / len(all_distances),
        "max_team_to_venue_distance_km": max(all_distances),
        "mean_group_distance_std_km": sum(group_stds) / len(group_stds),
        "home_penalty_total": home_penalty,
        "strong_home_group_count": float(strong_home_groups),
        "propagation_benefit": propagation,
        "regional_balance_penalty": region_penalty,
    }


def write_venue_outputs(groups: GroupMap, teams: list[Team], output_dir: str | Path) -> dict[str, float]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    assignment = assign_reference_venues(groups)
    rows = venue_assignment_rows(groups, teams, assignment)
    write_csv(output_dir / "venue_assignment.csv", rows)
    metrics = venue_metrics(groups, teams, assignment)
    (output_dir / "venue_metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")

    grouped_by_venue: dict[str, list[dict[str, object]]] = {}
    for row in rows:
        grouped_by_venue.setdefault(str(row["venue"]), []).append(row)
    lines = [
        "# 问题三比赛地点选择结果",
        "",
        "模型在最终 D003 分组基础上选择 8 个比赛地点，每个地点承办 2 个小组。目标同时考虑参赛队出行距离、区域覆盖、县级承办普及面和主场公平性。",
        "",
        "## 推荐承办地",
        "",
        "台州市、宁波市、杭州市、温州市、绍兴市、金华市、青田县、龙游县。",
        "",
        "## 小组分配",
        "",
        "| 比赛地点 | 区域 | 承办小组 | 小组队伍 | 平均距离km | 最远距离km |",
        "|---|---|---|---|---:|---:|",
    ]
    for venue, venue_rows in grouped_by_venue.items():
        for row in venue_rows:
            lines.append(
                f"| {venue} | {row['region']} | {row['host_groups']} | {row['group_teams']} | "
                f"{row['avg_distance_km']} | {row['max_distance_km']} |"
            )
    lines.extend(
        [
            "",
            "## 综合指标",
            "",
            "| 指标 | 数值 |",
            "|---|---:|",
            f"| 覆盖区域数 | {metrics['covered_regions']:.0f} |",
            f"| 县级承办点数量 | {metrics['county_venue_count']:.0f} |",
            f"| 参赛队平均到赛地距离 | {metrics['avg_team_to_venue_distance_km']:.2f} km |",
            f"| 单队最远到赛地距离 | {metrics['max_team_to_venue_distance_km']:.2f} km |",
            f"| 小组出行距离标准差均值 | {metrics['mean_group_distance_std_km']:.2f} km |",
            f"| 主场关联惩罚合计 | {metrics['home_penalty_total']:.2f} |",
            f"| 强主场小组数 | {metrics['strong_home_group_count']:.0f} |",
            f"| 主场传播收益 | {metrics['propagation_benefit']:.4f} |",
            f"| 区域均衡惩罚 | {metrics['regional_balance_penalty']:.4f} |",
        ]
    )
    (output_dir / "venue_solution.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return metrics
