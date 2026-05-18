from __future__ import annotations

import argparse

from _bootstrap import ROOT
from math_model.grouping import generate_schemes, rank_with_topsis
from math_model.io import load_teams
from math_model.lottery import write_lottery_outputs
from math_model.pipeline import remove_verbose_markdown_outputs


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a public lottery pool and draw one scheme.")
    parser.add_argument("--teams", default=str(ROOT / "data" / "final_teams.csv"))
    parser.add_argument("--candidates", type=int, default=300)
    parser.add_argument("--top-k", type=int, default=100)
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--alpha", type=float, default=0.5, help="accepted for compatibility")
    parser.add_argument("--draw-seed", default="7392048615")
    parser.add_argument("--steps", type=int, default=200)
    parser.add_argument("--output-dir", default=str(ROOT / "results" / "03_公开抽签"))
    args = parser.parse_args()
    teams = load_teams(args.teams)
    schemes = generate_schemes(teams, candidates=args.candidates, seed=args.seed, steps=args.steps)
    for idx, row in enumerate(schemes, start=1):
        row["scheme_id"] = f"S{idx:04d}"
    ranked = rank_with_topsis(schemes, "topsis_score")
    record = write_lottery_outputs(ranked, teams, args.output_dir, top_k=min(args.top_k, len(ranked)), public_seed=str(args.draw_seed))
    remove_verbose_markdown_outputs(ROOT)
    print(f"Pool SHA-256: {record['pool_sha256']}")
    print(f"Selected: {record['selected_pool_id']} from {record['selected_source_scheme_id']}")


if __name__ == "__main__":
    main()
