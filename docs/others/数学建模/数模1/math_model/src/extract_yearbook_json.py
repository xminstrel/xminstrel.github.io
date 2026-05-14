from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import pandas as pd


def extract_payload(html_path: Path) -> dict:
    text = html_path.read_text(encoding="utf-8")
    match = re.search(r"var\s+data\s*=\s*(\{.*?\});\s*\n\s*\$\('\.book'\)", text, re.S)
    if not match:
        raise ValueError(f"Cannot find yearbook JSON payload in {html_path}")
    return json.loads(match.group(1))


def flatten_headers(rows: list[list[str]], fixed_rows_top: int) -> list[str]:
    header_rows = rows[:fixed_rows_top]
    max_cols = max(len(row) for row in header_rows)
    headers: list[str] = []
    for col in range(max_cols):
        parts = []
        for row in header_rows:
            value = row[col].strip() if col < len(row) and isinstance(row[col], str) else ""
            if value:
                parts.append(value)
        name = "__".join(parts) if parts else f"col_{col}"
        headers.append(name)
    return headers


def payload_to_dataframe(payload: dict) -> pd.DataFrame:
    rows = payload["data"]
    fixed_rows_top = int(payload.get("fixedRowsTop", 1))
    headers = flatten_headers(rows, fixed_rows_top)
    body = []
    for raw_row in rows[fixed_rows_top:]:
        row = list(raw_row) + [""] * (len(headers) - len(raw_row))
        if not any(str(value).strip() for value in row):
            continue
        if str(row[0]).strip().startswith("注"):
            continue
        body.append(row[: len(headers)])
    return pd.DataFrame(body, columns=headers)


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract Zhejiang Statistical Yearbook table JSON from official HTML.")
    parser.add_argument("inputs", nargs="+", type=Path)
    parser.add_argument("--out-dir", type=Path, default=Path("data/processed/yearbook"))
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    for html_path in args.inputs:
        payload = extract_payload(html_path)
        code = payload.get("num") or html_path.stem
        df = payload_to_dataframe(payload)
        json_path = args.out_dir / f"{code}.json"
        csv_path = args.out_dir / f"{code}.csv"
        json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        df.to_csv(csv_path, index=False, encoding="utf-8-sig")
        print(f"{code}: {len(df)} rows, {len(df.columns)} columns -> {csv_path}")


if __name__ == "__main__":
    main()
