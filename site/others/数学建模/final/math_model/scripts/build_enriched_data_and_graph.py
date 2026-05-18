from __future__ import annotations

import argparse

from _bootstrap import ROOT
from math_model.graph import write_graph_outputs
from math_model.io import load_teams
from math_model.pipeline import remove_verbose_markdown_outputs


def main() -> None:
    parser = argparse.ArgumentParser(description="Refresh data report and graph-coloring outputs.")
    parser.add_argument("--teams", default=str(ROOT / "data" / "final_teams.csv"))
    parser.add_argument("--output-dir", default=str(ROOT / "results" / "01_图染色"))
    args = parser.parse_args()
    teams = load_teams(args.teams)
    stats = write_graph_outputs(teams, args.output_dir)
    remove_verbose_markdown_outputs(ROOT)
    print(f"Teams: {len(teams)}")
    print(f"Conflict edges: {stats['edge_count']}")
    print(f"Graph conclusion: {stats['chromatic_number_conclusion']}")


if __name__ == "__main__":
    main()
