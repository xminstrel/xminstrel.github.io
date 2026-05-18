from __future__ import annotations

import argparse

from _bootstrap import ROOT
from math_model.grouping import read_scheme_csv
from math_model.io import load_teams
from math_model.pipeline import remove_verbose_markdown_outputs
from math_model.venues import write_venue_outputs


def main() -> None:
    parser = argparse.ArgumentParser(description="Assign eight venues to the selected grouping scheme.")
    parser.add_argument("--teams", default=str(ROOT / "data" / "final_teams.csv"))
    parser.add_argument("--groups", default=str(ROOT / "results" / "02_分组方案" / "selected_scheme.csv"))
    parser.add_argument("--output-dir", default=str(ROOT / "results" / "04_赛地选择"))
    parser.add_argument("--max-candidates", type=int, default=30, help="accepted for compatibility")
    parser.add_argument("--seed", type=int, default=2026, help="accepted for compatibility")
    parser.add_argument("--iterations", type=int, default=8000, help="accepted for compatibility")
    parser.add_argument("--profile", default="balanced", help="accepted for compatibility")
    args = parser.parse_args()
    teams = load_teams(args.teams)
    groups = read_scheme_csv(args.groups)
    metrics = write_venue_outputs(groups, teams, args.output_dir)
    remove_verbose_markdown_outputs(ROOT)
    print(f"Venue regions: {metrics['covered_regions']:.0f}")
    print(f"Average distance: {metrics['avg_team_to_venue_distance_km']:.2f} km")


if __name__ == "__main__":
    main()
