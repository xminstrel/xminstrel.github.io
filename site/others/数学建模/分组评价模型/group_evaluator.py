#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Zhejiang city-county football grouping evaluator.

The program generates feasible grouping schemes, calculates the indicators in
建模方案.md, ranks schemes by TOPSIS, and writes result files under outputs/.
It has no third-party dependency.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple


CITY_ORDER = [
    "杭州市",
    "宁波市",
    "温州市",
    "嘉兴市",
    "湖州市",
    "绍兴市",
    "金华市",
    "衢州市",
    "舟山市",
    "台州市",
    "丽水市",
]

COUNTIES = {
    "杭州市": ["建德市", "桐庐县", "淳安县"],
    "宁波市": ["余姚市", "慈溪市", "象山县", "宁海县"],
    "温州市": ["瑞安市", "乐清市", "龙港市", "永嘉县", "平阳县", "苍南县", "文成县", "泰顺县"],
    "嘉兴市": ["海宁市", "平湖市", "桐乡市", "嘉善县", "海盐县"],
    "湖州市": ["德清县", "长兴县", "安吉县"],
    "绍兴市": ["诸暨市", "嵊州市", "新昌县"],
    "金华市": ["兰溪市", "义乌市", "东阳市", "永康市", "武义县", "浦江县", "磐安县"],
    "衢州市": ["江山市", "常山县", "开化县", "龙游县"],
    "舟山市": ["岱山县", "嵊泗县"],
    "台州市": ["温岭市", "临海市", "玉环市", "三门县", "天台县", "仙居县"],
    "丽水市": ["龙泉市", "青田县", "缙云县", "遂昌县", "松阳县", "云和县", "庆元县", "景宁畲族自治县"],
}

# City-level proxy data. Replace these columns with official county/city data
# before final submission if you have collected them.
# Units: GDP=100 million yuan, population=10k persons, tourism_proxy=relative score.
CITY_PROXY = {
    "杭州市": dict(region="浙北", lon=120.1551, lat=30.2741, gdp=21860, population=1259, tourism=250),
    "宁波市": dict(region="浙东", lon=121.5503, lat=29.8739, gdp=18147, population=969, tourism=190),
    "温州市": dict(region="浙南", lon=120.6994, lat=27.9949, gdp=9718, population=976, tourism=175),
    "嘉兴市": dict(region="浙北", lon=120.7555, lat=30.7461, gdp=7628, population=558, tourism=135),
    "湖州市": dict(region="浙北", lon=120.0868, lat=30.8944, gdp=4351, population=344, tourism=120),
    "绍兴市": dict(region="浙东", lon=120.5821, lat=29.9971, gdp=7791, population=539, tourism=145),
    "金华市": dict(region="浙中", lon=119.6495, lat=29.0895, gdp=6600, population=713, tourism=160),
    "衢州市": dict(region="浙西", lon=118.8726, lat=28.9417, gdp=2245, population=230, tourism=90),
    "舟山市": dict(region="浙东", lon=122.2072, lat=29.9853, gdp=2100, population=117, tourism=115),
    "台州市": dict(region="浙南", lon=121.4208, lat=28.6557, gdp=6400, population=671, tourism=135),
    "丽水市": dict(region="浙西南", lon=119.9229, lat=28.4672, gdp=2000, population=251, tourism=110),
}

GROUP_NAMES = [f"G{i:02d}" for i in range(1, 17)]
GROUP_CAPACITY = [3] * 11 + [4] * 5


@dataclass(frozen=True)
class Team:
    team_id: str
    name: str
    level: str
    parent_city: str
    region: str
    lon: float
    lat: float
    gdp: float
    population: float
    tourism: float
    football_facility: float
    youth_football: float
    sports_investment: float
    data_quality: str


def stable_factor(text: str, low: float, high: float) -> float:
    total = sum((idx + 1) * ord(ch) for idx, ch in enumerate(text))
    ratio = (total % 997) / 996
    return low + (high - low) * ratio


def build_default_teams() -> List[Team]:
    teams: List[Team] = []
    for city_idx, city in enumerate(CITY_ORDER, start=1):
        base = CITY_PROXY[city]
        # City team uses the city-level value directly.
        teams.append(
            Team(
                team_id=f"T{len(teams) + 1:02d}",
                name=city,
                level="city",
                parent_city=city,
                region=base["region"],
                lon=base["lon"],
                lat=base["lat"],
                gdp=base["gdp"],
                population=base["population"],
                tourism=base["tourism"],
                football_facility=0.55 * base["gdp"] / 100 + stable_factor(city, 20, 35),
                youth_football=0.04 * base["population"] + stable_factor(city, 15, 30),
                sports_investment=0.35 * base["gdp"] / 100 + stable_factor(city, 20, 30),
                data_quality="city_level_proxy",
            )
        )
        n_counties = len(COUNTIES[city])
        for county_idx, county in enumerate(COUNTIES[city], start=1):
            angle = 2 * math.pi * county_idx / max(n_counties, 1)
            radius = 0.18 + 0.035 * (county_idx % 4)
            scale = stable_factor(county, 0.45, 0.85)
            teams.append(
                Team(
                    team_id=f"T{len(teams) + 1:02d}",
                    name=county,
                    level="county",
                    parent_city=city,
                    region=base["region"],
                    lon=base["lon"] + radius * math.cos(angle),
                    lat=base["lat"] + radius * math.sin(angle),
                    gdp=base["gdp"] * scale / max(n_counties, 1),
                    population=base["population"] * stable_factor(county + "p", 0.55, 1.15) / max(n_counties, 1),
                    tourism=base["tourism"] * stable_factor(county + "t", 0.55, 1.30) / max(n_counties, 1),
                    football_facility=0.35 * base["gdp"] * scale / 100 / max(n_counties, 1)
                    + stable_factor(county + "f", 10, 35),
                    youth_football=0.03 * base["population"] / max(n_counties, 1) + stable_factor(county + "y", 10, 35),
                    sports_investment=0.25 * base["gdp"] * scale / 100 / max(n_counties, 1)
                    + stable_factor(county + "i", 10, 30),
                    data_quality="county_proxy_replace_with_official_data",
                )
            )
    return teams


def write_team_template(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    teams = build_default_teams()
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(teams[0].__dict__.keys()))
        writer.writeheader()
        for team in teams:
            writer.writerow(team.__dict__)


def load_teams(path: Path | None) -> List[Team]:
    if path and path.exists():
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            rows = list(csv.DictReader(f))
        teams = []
        for row in rows:
            teams.append(
                Team(
                    team_id=row["team_id"],
                    name=row["name"],
                    level=row["level"],
                    parent_city=row["parent_city"],
                    region=row["region"],
                    lon=float(row["lon"]),
                    lat=float(row["lat"]),
                    gdp=float(row["gdp"]),
                    population=float(row["population"]),
                    tourism=float(row["tourism"]),
                    football_facility=float(row["football_facility"]),
                    youth_football=float(row["youth_football"]),
                    sports_investment=float(row["sports_investment"]),
                    data_quality=row.get("data_quality", "unknown"),
                )
            )
        return teams
    return build_default_teams()


def normalize_by_team(teams: Sequence[Team], attr: str) -> Dict[str, float]:
    values = [getattr(t, attr) for t in teams]
    lo, hi = min(values), max(values)
    if math.isclose(lo, hi):
        return {t.team_id: 0.5 for t in teams}
    return {t.team_id: (getattr(t, attr) - lo) / (hi - lo) for t in teams}


def team_strength_scores(teams: Sequence[Team]) -> Dict[str, float]:
    f = normalize_by_team(teams, "football_facility")
    y = normalize_by_team(teams, "youth_football")
    invest = normalize_by_team(teams, "sports_investment")
    pop = normalize_by_team(teams, "population")
    gdp = normalize_by_team(teams, "gdp")
    return {
        t.team_id: 100 * (0.35 * f[t.team_id] + 0.25 * y[t.team_id] + 0.20 * invest[t.team_id] + 0.10 * pop[t.team_id] + 0.10 * gdp[t.team_id])
        for t in teams
    }


def attention_scores(teams: Sequence[Team]) -> Dict[str, float]:
    pop = normalize_by_team(teams, "population")
    gdp = normalize_by_team(teams, "gdp")
    tour = normalize_by_team(teams, "tourism")
    return {t.team_id: 100 * (0.40 * pop[t.team_id] + 0.30 * gdp[t.team_id] + 0.30 * tour[t.team_id]) for t in teams}


def cv(values: Sequence[float]) -> float:
    mean = sum(values) / len(values)
    if math.isclose(mean, 0.0):
        return 0.0
    var = sum((x - mean) ** 2 for x in values) / len(values)
    return math.sqrt(var) / mean


def variance(values: Sequence[float]) -> float:
    mean = sum(values) / len(values)
    return sum((x - mean) ** 2 for x in values) / len(values)


def haversine_km(a: Team, b: Team) -> float:
    radius = 6371.0
    lat1, lat2 = math.radians(a.lat), math.radians(b.lat)
    dlat = math.radians(b.lat - a.lat)
    dlon = math.radians(b.lon - a.lon)
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * radius * math.asin(math.sqrt(h))


def pairwise(group: Sequence[str]) -> Iterable[Tuple[str, str]]:
    for i in range(len(group)):
        for j in range(i + 1, len(group)):
            yield group[i], group[j]


def initial_groups(teams: Sequence[Team]) -> Tuple[List[List[str]], List[int], List[set]]:
    by_name = {t.name: t for t in teams}
    groups = [[] for _ in GROUP_NAMES]
    remaining = GROUP_CAPACITY[:]
    city_sets = [set() for _ in GROUP_NAMES]
    for idx, city in enumerate(CITY_ORDER):
        team = by_name[city]
        groups[idx].append(team.team_id)
        city_sets[idx].add(city)
    return groups, remaining, city_sets


def generate_one_scheme(teams: Sequence[Team], rng: random.Random, strict_no_same_city: bool = True) -> List[List[str]] | None:
    county_teams = [t for t in teams if t.level == "county"]
    team_by_id = {t.team_id: t for t in teams}
    groups, remaining, group_cities = initial_groups(teams)

    # High-county-count cities are harder to place; try them earlier.
    city_size = {city: len(items) for city, items in COUNTIES.items()}
    unassigned = sorted(county_teams, key=lambda t: (-city_size[t.parent_city], stable_factor(t.name, 0, 1)))

    def feasible_groups(team: Team) -> List[int]:
        result = []
        for g in range(16):
            if remaining[g] <= 0:
                continue
            if g < 11 and CITY_ORDER[g] == team.parent_city:
                continue
            if strict_no_same_city and team.parent_city in group_cities[g]:
                continue
            result.append(g)
        rng.shuffle(result)
        result.sort(key=lambda idx: (remaining[idx], len(group_cities[idx])), reverse=True)
        return result

    def search(left: List[Team]) -> bool:
        if not left:
            return True

        # Minimum remaining values heuristic.
        scored = [(len(feasible_groups(t)), rng.random(), t) for t in left]
        scored.sort(key=lambda x: (x[0], x[1]))
        if scored[0][0] == 0:
            return False
        team = scored[0][2]
        next_left = [t for t in left if t.team_id != team.team_id]

        for g in feasible_groups(team):
            groups[g].append(team.team_id)
            remaining[g] -= 1
            added_city = team.parent_city not in group_cities[g]
            group_cities[g].add(team.parent_city)
            if search(next_left):
                return True
            groups[g].pop()
            remaining[g] += 1
            if added_city:
                still_present = any(team_by_id[tid].parent_city == team.parent_city for tid in groups[g])
                if not still_present:
                    group_cities[g].remove(team.parent_city)
        return False

    return groups if search(unassigned) else None


def scheme_key(groups: Sequence[Sequence[str]]) -> str:
    # G01-G11 are fixed by city teams. G12-G16 can be canonicalized to reduce duplicates.
    first = [".".join(sorted(g)) for g in groups[:11]]
    last = sorted(".".join(sorted(g)) for g in groups[11:])
    return "|".join(first + last)


def generate_candidate_schemes(teams: Sequence[Team], count: int, seed: int, strict_no_same_city: bool) -> List[List[List[str]]]:
    rng = random.Random(seed)
    schemes: List[List[List[str]]] = []
    seen = set()
    max_attempts = max(500, count * 80)
    for _ in range(max_attempts):
        if len(schemes) >= count:
            break
        scheme = generate_one_scheme(teams, rng, strict_no_same_city=strict_no_same_city)
        if not scheme:
            continue
        key = scheme_key(scheme)
        if key in seen:
            continue
        seen.add(key)
        schemes.append([group[:] for group in scheme])
    return schemes


def hard_violations(groups: Sequence[Sequence[str]], teams: Sequence[Team]) -> int:
    by_id = {t.team_id: t for t in teams}
    violations = 0
    all_ids = [tid for group in groups for tid in group]
    violations += abs(len(all_ids) - len(set(all_ids)))
    violations += sum(abs(len(group) - 4) for group in groups)
    for group in groups:
        city_team_count = sum(1 for tid in group if by_id[tid].level == "city")
        if city_team_count > 1:
            violations += city_team_count - 1
        city_parents = {by_id[tid].parent_city for tid in group if by_id[tid].level == "city"}
        for tid in group:
            t = by_id[tid]
            if t.level == "county" and t.parent_city in city_parents:
                violations += 1
    return violations


def evaluate_scheme(groups: Sequence[Sequence[str]], teams: Sequence[Team]) -> Dict[str, float]:
    by_id = {t.team_id: t for t in teams}
    strength = team_strength_scores(teams)
    attention = attention_scores(teams)

    same_city_repeat = 0.0
    pair_conflict = 0.0
    admin_diversities = []
    group_strengths = []
    eco_sums = []
    pop_sums = []
    tour_sums = []
    comp_values = []
    hot_match = 0.0
    group_distances = []
    region_counts = []

    for group in groups:
        teams_in_group = [by_id[tid] for tid in group]
        county_city_counter = Counter(t.parent_city for t in teams_in_group if t.level == "county")
        same_city_repeat += sum(max(0, n - 1) for n in county_city_counter.values())
        pair_conflict += sum(n * (n - 1) / 2 for n in county_city_counter.values())
        admin_diversities.append(len(set(t.parent_city for t in teams_in_group)))
        group_strengths.append(sum(strength[t.team_id] for t in teams_in_group))
        eco_sums.append(sum(t.gdp for t in teams_in_group))
        pop_sums.append(sum(t.population for t in teams_in_group))
        tour_sums.append(sum(t.tourism for t in teams_in_group))
        region_counts.append(len(set(t.region for t in teams_in_group)))

        suspense = []
        distances = []
        for a_id, b_id in pairwise(group):
            suspense.append(1.0 / (1.0 + abs(strength[a_id] - strength[b_id])))
            hot_match += math.sqrt(max(attention[a_id], 0) * max(attention[b_id], 0))
            distances.append(haversine_km(by_id[a_id], by_id[b_id]))
        comp_values.append(sum(suspense) / len(suspense))
        group_distances.append(sum(distances) / len(distances))

    return {
        "hard_violations": hard_violations(groups, teams),
        "same_city_repeat_index": same_city_repeat,
        "pair_conflict_index": pair_conflict,
        "admin_diversity": sum(admin_diversities) / len(admin_diversities),
        "sport_variance": variance(group_strengths),
        "sport_range": max(group_strengths) - min(group_strengths),
        "competition_suspense": sum(comp_values) / len(comp_values),
        "hot_match_index": hot_match,
        "eco_cv": cv(eco_sums),
        "pop_cv": cv(pop_sums),
        "tour_cv": cv(tour_sums),
        "avg_inner_distance_km": sum(group_distances) / len(group_distances),
        "geo_cover": sum(region_counts) / len(region_counts),
    }


METRIC_DIRECTIONS = {
    "same_city_repeat_index": "cost",
    "pair_conflict_index": "cost",
    "admin_diversity": "benefit",
    "sport_variance": "cost",
    "sport_range": "cost",
    "competition_suspense": "benefit",
    "hot_match_index": "benefit",
    "eco_cv": "cost",
    "pop_cv": "cost",
    "tour_cv": "cost",
    "avg_inner_distance_km": "cost",
    "geo_cover": "benefit",
}

DEFAULT_AHP_WEIGHTS = {
    "same_city_repeat_index": 0.10,
    "pair_conflict_index": 0.08,
    "admin_diversity": 0.07,
    "sport_variance": 0.13,
    "sport_range": 0.08,
    "competition_suspense": 0.10,
    "hot_match_index": 0.06,
    "eco_cv": 0.07,
    "pop_cv": 0.07,
    "tour_cv": 0.06,
    "avg_inner_distance_km": 0.12,
    "geo_cover": 0.06,
}


def positive_normalize(rows: Sequence[Dict[str, float]], metrics: Sequence[str]) -> List[Dict[str, float]]:
    normalized = []
    limits = {m: (min(row[m] for row in rows), max(row[m] for row in rows)) for m in metrics}
    for row in rows:
        z = {}
        for metric in metrics:
            lo, hi = limits[metric]
            if math.isclose(lo, hi):
                z[metric] = 1.0
            elif METRIC_DIRECTIONS[metric] == "benefit":
                z[metric] = (row[metric] - lo) / (hi - lo)
            else:
                z[metric] = (hi - row[metric]) / (hi - lo)
        normalized.append(z)
    return normalized


def entropy_weights(z_rows: Sequence[Dict[str, float]], metrics: Sequence[str]) -> Dict[str, float]:
    eps = 1e-12
    n = len(z_rows)
    if n <= 1:
        return {m: 1 / len(metrics) for m in metrics}
    d_values = {}
    for metric in metrics:
        col = [max(row[metric], 0.0) + eps for row in z_rows]
        total = sum(col)
        p = [x / total for x in col]
        entropy = -sum(x * math.log(x) for x in p) / math.log(n)
        d_values[metric] = max(0.0, 1 - entropy)
    d_total = sum(d_values.values())
    if math.isclose(d_total, 0.0):
        return {m: 1 / len(metrics) for m in metrics}
    return {m: d_values[m] / d_total for m in metrics}


def combined_weights(z_rows: Sequence[Dict[str, float]], metrics: Sequence[str], alpha: float) -> Dict[str, float]:
    e = entropy_weights(z_rows, metrics)
    ahp_sum = sum(DEFAULT_AHP_WEIGHTS[m] for m in metrics)
    ahp = {m: DEFAULT_AHP_WEIGHTS[m] / ahp_sum for m in metrics}
    raw = {m: alpha * ahp[m] + (1 - alpha) * e[m] for m in metrics}
    total = sum(raw.values())
    return {m: raw[m] / total for m in metrics}


def topsis_scores(z_rows: Sequence[Dict[str, float]], metrics: Sequence[str], weights: Dict[str, float]) -> List[float]:
    weighted = [{m: row[m] * weights[m] for m in metrics} for row in z_rows]
    ideal_pos = {m: max(row[m] for row in weighted) for m in metrics}
    ideal_neg = {m: min(row[m] for row in weighted) for m in metrics}
    scores = []
    for row in weighted:
        d_pos = math.sqrt(sum((row[m] - ideal_pos[m]) ** 2 for m in metrics))
        d_neg = math.sqrt(sum((row[m] - ideal_neg[m]) ** 2 for m in metrics))
        scores.append(d_neg / (d_pos + d_neg) if not math.isclose(d_pos + d_neg, 0.0) else 1.0)
    return scores


def stability_scores(
    z_rows: Sequence[Dict[str, float]],
    metrics: Sequence[str],
    base_weights: Dict[str, float],
    seed: int,
    simulations: int = 100,
    top_k_ratio: float = 0.10,
) -> List[float]:
    rng = random.Random(seed + 10000)
    n = len(z_rows)
    top_k = max(1, math.ceil(n * top_k_ratio))
    hit_counts = [0] * n
    for _ in range(simulations):
        raw = {m: base_weights[m] * rng.uniform(0.8, 1.2) for m in metrics}
        total = sum(raw.values())
        weights = {m: raw[m] / total for m in metrics}
        scores = topsis_scores(z_rows, metrics, weights)
        top_ids = sorted(range(n), key=lambda i: scores[i], reverse=True)[:top_k]
        for i in top_ids:
            hit_counts[i] += 1
    return [x / simulations for x in hit_counts]


def scheme_to_named(groups: Sequence[Sequence[str]], teams: Sequence[Team]) -> Dict[str, List[str]]:
    by_id = {t.team_id: t for t in teams}
    return {GROUP_NAMES[i]: [by_id[tid].name for tid in group] for i, group in enumerate(groups)}


def write_best_scheme_md(path: Path, best: Dict[str, object], teams: Sequence[Team], weights: Dict[str, float]) -> None:
    groups = best["groups"]
    named = scheme_to_named(groups, teams)
    lines = [
        "# 最优分组方案",
        "",
        f"方案编号：{best['scheme_id']}",
        f"TOPSIS 贴近度：{best['topsis_score']:.6f}",
        f"权重扰动稳定性：{best['stability']:.2%}",
        "",
        "## 分组结果",
        "",
        "| 小组 | 队伍 |",
        "|---|---|",
    ]
    for group_name in GROUP_NAMES:
        lines.append(f"| {group_name} | {'、'.join(named[group_name])} |")
    lines.extend(["", "## 指标值", "", "| 指标 | 数值 |", "|---|---:|"])
    for metric in ["hard_violations", *METRIC_DIRECTIONS.keys(), "stability", "topsis_score"]:
        if metric in best:
            value = best[metric]
            if isinstance(value, float):
                lines.append(f"| {metric} | {value:.6f} |")
            else:
                lines.append(f"| {metric} | {value} |")
    lines.extend(["", "## 综合权重", "", "| 指标 | 权重 |", "|---|---:|"])
    for metric, value in weights.items():
        lines.append(f"| {metric} | {value:.6f} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_scheme_csv(path: Path, groups: Sequence[Sequence[str]], teams: Sequence[Team]) -> None:
    by_id = {t.team_id: t for t in teams}
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["group", "slot", "team_id", "team_name", "level", "parent_city", "region"])
        for g_idx, group in enumerate(groups):
            for slot, tid in enumerate(group, start=1):
                t = by_id[tid]
                writer.writerow([GROUP_NAMES[g_idx], slot, t.team_id, t.name, t.level, t.parent_city, t.region])


def write_top_schemes_comparison(path: Path, rows: Sequence[Dict[str, object]], teams: Sequence[Team], top_n: int = 5) -> None:
    chosen = list(rows[:top_n])
    metric_labels = {
        "topsis_score": "综合得分",
        "stability": "稳定性",
        "sport_variance": "实力方差",
        "sport_range": "实力极差",
        "competition_suspense": "竞争悬念",
        "hot_match_index": "热点指数",
        "eco_cv": "经济CV",
        "pop_cv": "人口CV",
        "tour_cv": "文旅CV",
        "avg_inner_distance_km": "平均距离km",
        "geo_cover": "地域覆盖",
    }
    lines = [
        "# 若干可行分组方案对比",
        "",
        f"从候选池中按 TOPSIS 贴近度选取前 {len(chosen)} 个方案进行比较。所有方案均满足硬约束，且默认满足同市县级队不重复的强筛选条件。",
        "",
        "## 综合指标对比",
        "",
        "| 排名 | 方案 | 综合得分 | 稳定性 | 实力方差 | 实力极差 | 竞争悬念 | 热点指数 | 经济CV | 人口CV | 文旅CV | 平均距离km | 地域覆盖 |",
        "|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for rank, row in enumerate(chosen, start=1):
        lines.append(
            "| "
            + " | ".join(
                [
                    str(rank),
                    str(row["scheme_id"]),
                    f"{row['topsis_score']:.6f}",
                    f"{row['stability']:.2%}",
                    f"{row['sport_variance']:.2f}",
                    f"{row['sport_range']:.2f}",
                    f"{row['competition_suspense']:.6f}",
                    f"{row['hot_match_index']:.2f}",
                    f"{row['eco_cv']:.4f}",
                    f"{row['pop_cv']:.4f}",
                    f"{row['tour_cv']:.4f}",
                    f"{row['avg_inner_distance_km']:.2f}",
                    f"{row['geo_cover']:.4f}",
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## 方案解读",
            "",
            "- 综合得分越高，表示方案越接近多指标理想解。",
            "- 实力方差、实力极差、经济CV、人口CV、文旅CV、平均距离越小越好。",
            "- 竞争悬念、热点指数、地域覆盖、稳定性越大越好。",
            "- 若两个方案综合得分接近，可按论文侧重点选择：重公平则优先实力均衡，重传播则优先热点指数和地域覆盖，重办赛便利则优先平均距离。",
            "",
        ]
    )
    for rank, row in enumerate(chosen, start=1):
        named = scheme_to_named(row["groups"], teams)
        lines.extend(
            [
                f"## 方案 {rank}：{row['scheme_id']}",
                "",
                "| 小组 | 队伍 |",
                "|---|---|",
            ]
        )
        for group_name in GROUP_NAMES:
            lines.append(f"| {group_name} | {'、'.join(named[group_name])} |")
        lines.append("")
        lines.append("| 指标 | 数值 |")
        lines.append("|---|---:|")
        for metric, label in metric_labels.items():
            value = row[metric]
            if metric == "stability":
                lines.append(f"| {label} | {value:.2%} |")
            else:
                lines.append(f"| {label} | {value:.6f} |")
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate and evaluate Zhejiang city-county football grouping schemes.")
    parser.add_argument("--teams", type=Path, default=Path("data/teams.csv"), help="team feature CSV; fallback data is used if missing")
    parser.add_argument("--write-template", action="store_true", help="write the default replaceable team data template")
    parser.add_argument("--candidates", type=int, default=300, help="number of candidate schemes to generate")
    parser.add_argument("--seed", type=int, default=2026, help="random seed")
    parser.add_argument("--alpha", type=float, default=0.5, help="AHP weight share in AHP-entropy combination")
    parser.add_argument("--allow-repeat-city-counties", action="store_true", help="do not enforce n_ig <= 1 during generation")
    parser.add_argument("--output-dir", type=Path, default=Path("outputs"), help="output directory")
    args = parser.parse_args()

    if args.write_template:
        write_team_template(args.teams)
        print(f"Wrote team data template: {args.teams}")

    teams = load_teams(args.teams)
    if len(teams) != 64:
        raise SystemExit(f"Expected 64 teams, got {len(teams)}")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    schemes = generate_candidate_schemes(
        teams=teams,
        count=args.candidates,
        seed=args.seed,
        strict_no_same_city=not args.allow_repeat_city_counties,
    )
    if not schemes:
        raise SystemExit("No feasible scheme generated. Check constraints or team data.")

    rows = []
    for idx, scheme in enumerate(schemes, start=1):
        row = evaluate_scheme(scheme, teams)
        row["scheme_id"] = f"S{idx:04d}"
        row["groups"] = scheme
        rows.append(row)

    legal_rows = [row for row in rows if row["hard_violations"] == 0]
    if not legal_rows:
        raise SystemExit("Generated schemes all violate hard constraints.")

    metrics = list(METRIC_DIRECTIONS.keys())
    z_rows = positive_normalize(legal_rows, metrics)
    weights = combined_weights(z_rows, metrics, alpha=args.alpha)
    scores = topsis_scores(z_rows, metrics, weights)
    stability = stability_scores(z_rows, metrics, weights, seed=args.seed)

    for row, score, stable in zip(legal_rows, scores, stability):
        row["topsis_score"] = score
        row["stability"] = stable
    legal_rows.sort(key=lambda r: (r["topsis_score"], r["stability"]), reverse=True)

    ranking_path = args.output_dir / "ranking.csv"
    with ranking_path.open("w", encoding="utf-8-sig", newline="") as f:
        fieldnames = ["rank", "scheme_id", "topsis_score", "stability", "hard_violations", *metrics]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for rank, row in enumerate(legal_rows, start=1):
            writer.writerow({name: row.get(name, rank if name == "rank" else "") for name in fieldnames})

    json_path = args.output_dir / "candidate_schemes.json"
    serializable = []
    for row in legal_rows:
        item = {k: v for k, v in row.items() if k != "groups"}
        item["groups"] = scheme_to_named(row["groups"], teams)
        serializable.append(item)
    json_path.write_text(json.dumps(serializable, ensure_ascii=False, indent=2), encoding="utf-8")

    best = legal_rows[0]
    write_best_scheme_md(args.output_dir / "best_scheme.md", best, teams, weights)
    write_scheme_csv(args.output_dir / "best_scheme.csv", best["groups"], teams)
    write_top_schemes_comparison(args.output_dir / "top_schemes_comparison.md", legal_rows, teams, top_n=5)
    (args.output_dir / "weights.json").write_text(json.dumps(weights, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Generated schemes: {len(schemes)}")
    print(f"Legal schemes: {len(legal_rows)}")
    print(f"Best scheme: {best['scheme_id']}, TOPSIS={best['topsis_score']:.6f}, stability={best['stability']:.2%}")
    print(f"Wrote: {ranking_path}")
    print(f"Wrote: {args.output_dir / 'best_scheme.md'}")
    print(f"Wrote: {args.output_dir / 'top_schemes_comparison.md'}")


if __name__ == "__main__":
    main()
