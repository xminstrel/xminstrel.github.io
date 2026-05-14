from __future__ import annotations

import argparse

from _bootstrap import ROOT
from math_model.io import load_teams
from math_model.pipeline import remove_verbose_markdown_outputs, write_direct_outputs


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate and rank feasible group schemes.")
    parser.add_argument("--teams", default=str(ROOT / "data" / "final_teams.csv"))
    parser.add_argument("--starts", type=int, default=80)
    parser.add_argument("--steps", type=int, default=400)
    parser.add_argument("--keep", type=int, default=5)
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--initial-pool", type=int, default=None, help="accepted for compatibility; uses --starts")
    parser.add_argument("--output-dir", default=str(ROOT / "results" / "02_分组方案"))
    args = parser.parse_args()
    teams = load_teams(args.teams)
    rows = write_direct_outputs(teams, args.output_dir, starts=args.starts, steps=args.steps, keep=args.keep, seed=args.seed)
    remove_verbose_markdown_outputs(ROOT)
    best = max(rows, key=lambda row: float(row["elite_topsis"]))
    print(f"Generated {len(rows)} elite schemes.")
    print(f"Selected by TOPSIS: {best['scheme_id']} ({float(best['elite_topsis']):.6f})")


if __name__ == "__main__":
    main()
