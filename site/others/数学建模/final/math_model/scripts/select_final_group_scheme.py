from __future__ import annotations

import argparse

from _bootstrap import ROOT
from math_model.io import load_teams
from math_model.pipeline import remove_verbose_markdown_outputs, write_selection_outputs


def main() -> None:
    parser = argparse.ArgumentParser(description="Select the final grouping scheme by TOPSIS.")
    parser.add_argument("--teams", default=str(ROOT / "data" / "final_teams.csv"))
    parser.add_argument("--direct-json", default=str(ROOT / "results" / "02_分组方案" / "direct_top_schemes.json"))
    parser.add_argument("--output-dir", default=str(ROOT / "results" / "02_分组方案"))
    args = parser.parse_args()
    teams = load_teams(args.teams)
    selected = write_selection_outputs(teams, args.direct_json, args.output_dir)
    remove_verbose_markdown_outputs(ROOT)
    print(f"Selected scheme: {selected['scheme_id']} ({float(selected['elite_topsis']):.6f})")


if __name__ == "__main__":
    main()
