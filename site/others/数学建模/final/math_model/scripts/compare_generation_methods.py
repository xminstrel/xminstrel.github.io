from __future__ import annotations

import argparse
import json

from _bootstrap import ROOT
from math_model.grouping import generate_schemes, rank_with_topsis
from math_model.io import load_teams
from math_model.pipeline import remove_verbose_markdown_outputs, write_method_compare_outputs


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare direct search and candidate-pool generation.")
    parser.add_argument("--teams", default=str(ROOT / "data" / "final_teams.csv"))
    parser.add_argument("--direct-json", default=str(ROOT / "results" / "02_分组方案" / "direct_top_schemes.json"))
    parser.add_argument("--candidate-count", type=int, default=120)
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--output-dir", default=str(ROOT / "results" / "02_分组方案"))
    args = parser.parse_args()
    teams = load_teams(args.teams)
    direct_rows = json.loads(open(args.direct_json, "r", encoding="utf-8").read())
    candidates = generate_schemes(teams, candidates=args.candidate_count, seed=args.seed, steps=150)
    for idx, row in enumerate(candidates, start=1):
        row["scheme_id"] = f"S{idx:04d}"
    ranked = rank_with_topsis(candidates, "topsis_score")
    write_method_compare_outputs(direct_rows, ranked, args.output_dir)
    remove_verbose_markdown_outputs(ROOT)
    print(ROOT / "results" / "02_分组方案" / "method_compare.json")


if __name__ == "__main__":
    main()
