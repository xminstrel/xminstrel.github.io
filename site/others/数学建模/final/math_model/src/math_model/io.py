from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping


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
    data_quality: str = ""


def load_teams(path: str | Path) -> list[Team]:
    path = Path(path)
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    teams: list[Team] = []
    for row in rows:
        teams.append(
            Team(
                team_id=row["team_id"].strip(),
                name=row["name"].strip(),
                level=row["level"].strip(),
                parent_city=row["parent_city"].strip(),
                region=row["region"].strip(),
                lon=float(row["lon"]),
                lat=float(row["lat"]),
                gdp=float(row["gdp"]),
                population=float(row["population"]),
                tourism=float(row["tourism"]),
                football_facility=float(row["football_facility"]),
                youth_football=float(row["youth_football"]),
                sports_investment=float(row["sports_investment"]),
                data_quality=row.get("data_quality", "").strip(),
            )
        )
    return teams


def team_lookup(teams: Iterable[Team]) -> dict[str, Team]:
    return {team.name: team for team in teams}


def write_csv(path: str | Path, rows: Iterable[Mapping[str, object]], fieldnames: list[str] | None = None) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    materialized = list(rows)
    if fieldnames is None:
        fieldnames = list(materialized[0].keys()) if materialized else []
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(materialized)


def write_json(path: str | Path, data: object) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
