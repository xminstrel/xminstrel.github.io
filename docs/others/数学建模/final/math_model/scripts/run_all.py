from __future__ import annotations

import argparse

from _bootstrap import ROOT
from math_model.pipeline import run_all


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the complete modeling pipeline.")
    parser.add_argument("--starts", type=int, default=80, help="number of direct-search starts")
    parser.add_argument("--steps", type=int, default=400, help="local-search swap steps per generated scheme")
    parser.add_argument("--lottery-candidates", type=int, default=300, help="candidate schemes for lottery pool")
    parser.add_argument("--sims", type=int, default=1000, help="Monte Carlo simulations per tournament format")
    args = parser.parse_args()
    run_all(ROOT, starts=args.starts, steps=args.steps, lottery_candidates=args.lottery_candidates, sims=args.sims)
    print("Pipeline completed.")
    print(ROOT / "results")


if __name__ == "__main__":
    main()
