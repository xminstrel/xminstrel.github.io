from __future__ import annotations

import argparse

from _bootstrap import ROOT
from math_model.grouping import read_scheme_csv
from math_model.io import load_teams
from math_model.pipeline import remove_verbose_markdown_outputs
from math_model.tournament import write_tournament_outputs


def main() -> None:
    parser = argparse.ArgumentParser(description="Run tournament-format Monte Carlo simulation.")
    parser.add_argument("--teams", default=str(ROOT / "data" / "final_teams.csv"))
    parser.add_argument("--groups", default=str(ROOT / "results" / "02_分组方案" / "selected_scheme.csv"))
    parser.add_argument("--venues", default=str(ROOT / "results" / "04_赛地选择" / "venue_assignment.csv"), help="accepted for compatibility")
    parser.add_argument("--sims", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--output-dir", default=str(ROOT / "results" / "05_赛制仿真"))
    args = parser.parse_args()
    teams = load_teams(args.teams)
    groups = read_scheme_csv(args.groups)
    rows = write_tournament_outputs(groups, teams, args.output_dir, sims=args.sims, seed=args.seed)
    remove_verbose_markdown_outputs(ROOT)
    print(f"Simulated {len(rows)} tournament formats with {args.sims} runs each.")


if __name__ == "__main__":
    main()
