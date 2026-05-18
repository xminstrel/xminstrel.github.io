from __future__ import annotations

import csv
import math
import random
from collections import Counter
from pathlib import Path

from .io import Team, team_lookup


GroupMap = dict[str, list[str]]

REFERENCE_GROUPS_D003: GroupMap = {
    "G01": ["杭州市", "江山市", "泰顺县", "东阳市"],
    "G02": ["宁波市", "三门县", "遂昌县", "淳安县"],
    "G03": ["温州市", "青田县", "开化县", "建德市"],
    "G04": ["嘉兴市", "永康市", "景宁畲族自治县", "平阳县"],
    "G05": ["湖州市", "义乌市", "云和县", "温岭市"],
    "G06": ["绍兴市", "桐乡市", "桐庐县", "磐安县"],
    "G07": ["金华市", "庆元县", "嘉善县", "仙居县"],
    "G08": ["衢州市", "天台县", "象山县", "龙泉市"],
    "G09": ["舟山市", "临海市", "德清县", "永嘉县"],
    "G10": ["台州市", "海盐县", "宁海县", "苍南县"],
    "G11": ["丽水市", "文成县", "海宁市", "新昌县"],
    "G12": ["松阳县", "乐清市", "浦江县", "嵊泗县"],
    "G13": ["龙游县", "兰溪市", "玉环市", "嵊州市"],
    "G14": ["瑞安市", "诸暨市", "武义县", "长兴县"],
    "G15": ["常山县", "余姚市", "安吉县", "缙云县"],
    "G16": ["龙港市", "平湖市", "岱山县", "慈溪市"],
}

METRIC_DIRECTIONS: dict[str, str] = {
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

DEFAULT_WEIGHTS: dict[str, float] = {
    "admin_diversity": 0.13,
    "sport_variance": 0.16,
    "sport_range": 0.10,
    "competition_suspense": 0.08,
    "hot_match_index": 0.09,
    "eco_cv": 0.09,
    "pop_cv": 0.08,
    "tour_cv": 0.06,
    "avg_inner_distance_km": 0.12,
    "geo_cover": 0.09,
}


def haversine_km(a: Team, b: Team) -> float:
    radius = 6371.0
    lat1, lon1 = math.radians(a.lat), math.radians(a.lon)
    lat2, lon2 = math.radians(b.lat), math.radians(b.lon)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * radius * math.asin(math.sqrt(h))


def _minmax(values: list[float]) -> list[float]:
    lo, hi = min(values), max(values)
    if math.isclose(lo, hi):
        return [50.0 for _ in values]
    return [(value - lo) / (hi - lo) * 100.0 for value in values]


def strength_scores(teams: list[Team]) -> dict[str, float]:
    raw = [
        0.34 * team.football_facility
        + 0.24 * team.youth_football
        + 0.26 * team.sports_investment
        + 0.10 * math.sqrt(max(team.gdp, 0.0))
        + 0.06 * math.sqrt(max(team.population, 0.0))
        for team in teams
    ]
    return {team.name: score for team, score in zip(teams, _minmax(raw))}


def cv(values: list[float]) -> float:
    mean = sum(values) / len(values)
    if math.isclose(mean, 0.0):
        return 0.0
    variance = sum((value - mean) ** 2 for value in values) / len(values)
    return math.sqrt(variance) / mean


def groups_to_rows(groups: GroupMap, teams: list[Team]) -> list[dict[str, object]]:
    by_name = team_lookup(teams)
    rows: list[dict[str, object]] = []
    for group in sorted(groups):
        for slot, name in enumerate(groups[group], start=1):
            team = by_name[name]
            rows.append(
                {
                    "group": group,
                    "slot": slot,
                    "team_id": team.team_id,
                    "team_name": team.name,
                    "level": team.level,
                    "parent_city": team.parent_city,
                    "region": team.region,
                }
            )
    return rows


def pair_conflicts(groups: GroupMap, teams: list[Team]) -> int:
    by_name = team_lookup(teams)
    conflicts = 0
    for names in groups.values():
        members = [by_name[name] for name in names]
        for i, a in enumerate(members):
            for b in members[i + 1 :]:
                same_parent = a.parent_city == b.parent_city
                both_city = a.level == "city" and b.level == "city"
                if same_parent or both_city:
                    conflicts += 1
    return conflicts


def hard_violations(groups: GroupMap, teams: list[Team]) -> int:
    by_name = team_lookup(teams)
    expected = set(by_name)
    assigned = [name for names in groups.values() for name in names]
    violations = abs(len(assigned) - len(expected)) + len(expected.symmetric_difference(assigned))
    violations += sum(abs(len(names) - 4) for names in groups.values())
    violations += pair_conflicts(groups, teams)
    return violations


def evaluate_scheme(groups: GroupMap, teams: list[Team]) -> dict[str, float]:
    by_name = team_lookup(teams)
    strengths = strength_scores(teams)
    group_strengths: list[float] = []
    group_gdp: list[float] = []
    group_pop: list[float] = []
    group_tour: list[float] = []
    group_regions: list[int] = []
    group_parent_unique: list[int] = []
    inner_distances: list[float] = []
    suspense_values: list[float] = []
    hot_values: list[float] = []

    for names in groups.values():
        members = [by_name[name] for name in names]
        member_strengths = [strengths[name] for name in names]
        group_strengths.append(sum(member_strengths) / len(member_strengths))
        group_gdp.append(sum(team.gdp for team in members))
        group_pop.append(sum(team.population for team in members))
        group_tour.append(sum(team.tourism for team in members))
        group_regions.append(len({team.region for team in members}))
        group_parent_unique.append(len({team.parent_city for team in members}))
        distances = [haversine_km(a, b) for i, a in enumerate(members) for b in members[i + 1 :]]
        inner_distances.extend(distances)
        strength_std = math.sqrt(sum((value - sum(member_strengths) / len(member_strengths)) ** 2 for value in member_strengths) / len(member_strengths))
        suspense_values.append(1.0 / (1.0 + strength_std / 18.0))
        team_heat = {
            team.name: 0.42 * math.log1p(team.gdp) + 0.30 * math.log1p(team.population) + 0.28 * math.log1p(team.tourism)
            for team in members
        }
        hot_values.append(sum(team_heat[a.name] * team_heat[b.name] for i, a in enumerate(members) for b in members[i + 1 :]) / 6.0)

    sport_mean = sum(group_strengths) / len(group_strengths)
    sport_variance = sum((value - sport_mean) ** 2 for value in group_strengths) / len(group_strengths)
    violations = hard_violations(groups, teams)
    pair_count = pair_conflicts(groups, teams)
    same_city_repeat = sum(max(0, 4 - unique_count) for unique_count in group_parent_unique)
    return {
        "hard_violations": float(violations),
        "same_city_repeat_index": float(same_city_repeat),
        "pair_conflict_index": float(pair_count),
        "admin_diversity": sum(group_parent_unique) / len(group_parent_unique),
        "sport_variance": sport_variance,
        "sport_range": max(group_strengths) - min(group_strengths),
        "competition_suspense": sum(suspense_values) / len(suspense_values),
        "hot_match_index": sum(hot_values) / len(hot_values),
        "eco_cv": cv(group_gdp),
        "pop_cv": cv(group_pop),
        "tour_cv": cv(group_tour),
        "avg_inner_distance_km": sum(inner_distances) / len(inner_distances),
        "geo_cover": sum(group_regions) / len(group_regions),
    }


def positive_normalize(rows: list[dict[str, float]], metrics: list[str]) -> list[dict[str, float]]:
    normalized: list[dict[str, float]] = []
    for row in rows:
        normalized.append(dict(row))

    for metric in metrics:
        values = [float(row[metric]) for row in rows]
        lo, hi = min(values), max(values)
        for target, value in zip(normalized, values):
            if math.isclose(lo, hi):
                target[metric] = 1.0
            elif METRIC_DIRECTIONS[metric] == "benefit":
                target[metric] = (value - lo) / (hi - lo)
            else:
                target[metric] = (hi - value) / (hi - lo)
    return normalized


def topsis_scores(rows: list[dict[str, float]], metrics: list[str], weights: dict[str, float] | None = None) -> list[float]:
    if weights is None:
        weights = DEFAULT_WEIGHTS
    normalized = positive_normalize(rows, metrics)
    scores: list[float] = []
    for row in normalized:
        positive = 0.0
        negative = 0.0
        for metric in metrics:
            weighted = row[metric] * weights[metric]
            positive += (weighted - weights[metric]) ** 2
            negative += weighted**2
        d_pos = math.sqrt(positive)
        d_neg = math.sqrt(negative)
        scores.append(d_neg / (d_pos + d_neg) if not math.isclose(d_pos + d_neg, 0.0) else 0.0)
    return scores


def direct_score(metrics: dict[str, float]) -> float:
    if metrics["hard_violations"] > 0:
        return -1000.0 - metrics["hard_violations"]
    utility = 0.0
    utility += 0.18 * (1.0 / (1.0 + metrics["sport_variance"] / 40.0))
    utility += 0.12 * (1.0 / (1.0 + metrics["sport_range"] / 18.0))
    utility += 0.10 * metrics["competition_suspense"]
    utility += 0.10 * (1.0 / (1.0 + metrics["avg_inner_distance_km"] / 190.0))
    utility += 0.10 * (metrics["geo_cover"] / 4.0)
    utility += 0.10 * (metrics["admin_diversity"] / 4.0)
    utility += 0.09 * (1.0 / (1.0 + metrics["eco_cv"]))
    utility += 0.08 * (1.0 / (1.0 + metrics["pop_cv"]))
    utility += 0.06 * (1.0 / (1.0 + metrics["tour_cv"]))
    utility += 0.07 * (1.0 / (1.0 + math.exp(-(metrics["hot_match_index"] - 20.0) / 10.0)))
    return utility


def _construct_feasible(teams: list[Team], rng: random.Random) -> GroupMap:
    groups: GroupMap = {f"G{i:02d}": [] for i in range(1, 17)}
    city_teams = [team for team in teams if team.level == "city"]
    county_teams = [team for team in teams if team.level != "city"]
    rng.shuffle(county_teams)

    for idx, team in enumerate(city_teams, start=1):
        groups[f"G{idx:02d}"].append(team.name)

    by_name = team_lookup(teams)

    def feasible_groups(candidate: Team) -> list[str]:
        out: list[str] = []
        for group, names in groups.items():
            members = [by_name[name] for name in names]
            if len(members) >= 4:
                continue
            if any(member.parent_city == candidate.parent_city for member in members):
                continue
            if candidate.level == "city" and any(member.level == "city" for member in members):
                continue
            out.append(group)
        return out

    def group_penalty(group: str, candidate: Team) -> float:
        members = [by_name[name] for name in groups[group]]
        if not members:
            return rng.random() * 0.15
        distance = sum(haversine_km(candidate, member) for member in members) / len(members)
        region_bonus = -12.0 if candidate.region not in {member.region for member in members} else 0.0
        size_pressure = len(members) * 6.0
        return distance + region_bonus + size_pressure + rng.random() * 60.0

    unplaced = list(county_teams)
    remaining_by_parent = Counter(team.parent_city for team in unplaced)

    def can_complete() -> bool:
        if sum(4 - len(names) for names in groups.values()) != len(unplaced):
            return False
        for parent, count in remaining_by_parent.items():
            if count <= 0:
                continue
            available = 0
            for names in groups.values():
                if len(names) < 4 and all(by_name[name].parent_city != parent for name in names):
                    available += 1
            if count > available:
                return False
        return True

    def search() -> bool:
        if not unplaced:
            return all(len(names) == 4 for names in groups.values())
        ranked_teams = sorted(
            unplaced,
            key=lambda team: (len(feasible_groups(team)), -remaining_by_parent[team.parent_city], rng.random()),
        )
        team = ranked_teams[0]
        candidates = feasible_groups(team)
        if not candidates:
            return False
        candidates.sort(key=lambda group: (len(groups[group]), group_penalty(group, team)))

        unplaced.remove(team)
        remaining_by_parent[team.parent_city] -= 1
        for group in candidates:
            groups[group].append(team.name)
            if can_complete() and search():
                return True
            groups[group].pop()
        remaining_by_parent[team.parent_city] += 1
        unplaced.append(team)
        return False

    if not search():
        raise RuntimeError("无法构造满足行政回避和每组 4 队的可行分组")
    return groups


def mutate_by_swaps(groups: GroupMap, teams: list[Team], rng: random.Random, steps: int = 300) -> GroupMap:
    current = {group: list(names) for group, names in groups.items()}
    current_score = direct_score(evaluate_scheme(current, teams))
    temperature = 0.06
    team_by_name = team_lookup(teams)

    def can_swap(group_a: str, idx_a: int, group_b: str, idx_b: int) -> bool:
        trial_a = list(current[group_a])
        trial_b = list(current[group_b])
        trial_a[idx_a], trial_b[idx_b] = trial_b[idx_b], trial_a[idx_a]
        for names in (trial_a, trial_b):
            members = [team_by_name[name] for name in names]
            if len({team.parent_city for team in members}) < len(members):
                return False
            if sum(1 for team in members if team.level == "city") > 1:
                return False
        return True

    groups_list = list(current)
    for step in range(steps):
        ga, gb = rng.sample(groups_list, 2)
        ia = rng.randrange(len(current[ga]))
        ib = rng.randrange(len(current[gb]))
        if not can_swap(ga, ia, gb, ib):
            continue
        current[ga][ia], current[gb][ib] = current[gb][ib], current[ga][ia]
        new_score = direct_score(evaluate_scheme(current, teams))
        accept = new_score >= current_score or rng.random() < math.exp((new_score - current_score) / max(temperature, 1e-6))
        if accept:
            current_score = new_score
        else:
            current[ga][ia], current[gb][ib] = current[gb][ib], current[ga][ia]
        temperature *= 0.995
    return current


def generate_schemes(teams: list[Team], candidates: int, seed: int, steps: int = 300) -> list[dict[str, object]]:
    rng = random.Random(seed)
    rows: list[dict[str, object]] = []

    def add_scheme(groups: GroupMap) -> None:
        metrics = evaluate_scheme(groups, teams)
        item: dict[str, object] = {**metrics}
        item["direct_score"] = direct_score(metrics)
        item["groups"] = groups
        rows.append(item)

    add_scheme(REFERENCE_GROUPS_D003)
    for _ in range(max(0, candidates - 1)):
        groups = _construct_feasible(teams, rng)
        groups = mutate_by_swaps(groups, teams, rng, steps=steps)
        add_scheme(groups)

    rows = [row for row in rows if row["hard_violations"] == 0]
    rows.sort(key=lambda row: float(row["direct_score"]), reverse=True)
    seen: set[tuple[tuple[str, ...], ...]] = set()
    unique: list[dict[str, object]] = []
    for row in rows:
        key = tuple(tuple(sorted(names)) for _, names in sorted(row["groups"].items()))  # type: ignore[union-attr]
        if key in seen:
            continue
        seen.add(key)
        unique.append(row)
    return unique


def rank_with_topsis(rows: list[dict[str, object]], score_name: str = "topsis_score") -> list[dict[str, object]]:
    metrics = list(METRIC_DIRECTIONS)
    numeric_rows = [{metric: float(row[metric]) for metric in metrics} for row in rows]
    scores = topsis_scores(numeric_rows, metrics)
    ranked: list[dict[str, object]] = []
    for row, score in zip(rows, scores):
        item = dict(row)
        item[score_name] = score
        ranked.append(item)
    ranked.sort(key=lambda row: float(row[score_name]), reverse=True)
    return ranked


def write_scheme_csv(path: str | Path, groups: GroupMap, teams: list[Team]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = groups_to_rows(groups, teams)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def read_scheme_csv(path: str | Path) -> GroupMap:
    groups: GroupMap = {}
    with Path(path).open("r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            groups.setdefault(row["group"], []).append(row["team_name"])
    return groups
