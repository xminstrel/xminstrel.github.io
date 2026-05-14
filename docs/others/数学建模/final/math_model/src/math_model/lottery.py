from __future__ import annotations

import csv
import hashlib
from dataclasses import asdict, dataclass
from pathlib import Path

from .grouping import GroupMap, rank_with_topsis, write_scheme_csv
from .io import Team, write_json


@dataclass(frozen=True)
class LotteryDraw:
    public_random_number: int
    public_seed: str
    random_source: str
    pool_size: int
    selected_index: int
    pool_sha256: str
    draw_rule: str = "R = int(SHA256(s | H), 16); q = (R mod K) + 1"


def draw_from_hash(pool_sha256: str, public_seed: str, pool_size: int) -> LotteryDraw:
    digest = hashlib.sha256(f"{public_seed}|{pool_sha256}".encode("utf-8")).hexdigest()
    number = int(digest, 16)
    return LotteryDraw(
        public_random_number=number,
        public_seed=public_seed,
        random_source=f"SHA256({public_seed}|{pool_sha256})={digest}",
        pool_size=pool_size,
        selected_index=number % pool_size + 1,
        pool_sha256=pool_sha256,
    )


def _scheme_rows_for_hash(pool: list[dict[str, object]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for idx, item in enumerate(pool, start=1):
        groups: GroupMap = item["groups"]  # type: ignore[assignment]
        for group in sorted(groups):
            rows.append(
                {
                    "pool_id": f"P{idx:04d}",
                    "source_scheme_id": item["scheme_id"],
                    "group": group,
                    "teams": "、".join(groups[group]),
                    "topsis_score": f"{float(item['topsis_score']):.6f}",
                }
            )
    return rows


def write_lottery_outputs(
    schemes: list[dict[str, object]],
    teams: list[Team],
    output_dir: str | Path,
    top_k: int = 100,
    public_seed: str = "7392048615",
) -> dict[str, object]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    ranked = rank_with_topsis(schemes, "topsis_score")[:top_k]
    for idx, item in enumerate(ranked, start=1):
        item["pool_id"] = f"P{idx:04d}"

    pool_rows = _scheme_rows_for_hash(ranked)
    pool_csv = output_dir / "scheme_pool.csv"
    with pool_csv.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(pool_rows[0].keys()))
        writer.writeheader()
        writer.writerows(pool_rows)
    digest = hashlib.sha256(pool_csv.read_bytes()).hexdigest()
    (output_dir / "scheme_pool.sha256").write_text(digest + "\n", encoding="utf-8")

    draw = draw_from_hash(digest, public_seed, len(ranked))
    selected = ranked[draw.selected_index - 1]
    selected_groups: GroupMap = selected["groups"]  # type: ignore[assignment]
    write_scheme_csv(output_dir / "final_draw_scheme.csv", selected_groups, teams)

    draw_record = {
        **asdict(draw),
        "selected_pool_id": selected["pool_id"],
        "selected_source_scheme_id": selected["scheme_id"],
        "selected_topsis_score": selected["topsis_score"],
    }
    write_json(output_dir / "draw_record.json", draw_record)
    write_json(output_dir / "scheme_pool.json", ranked)

    lines = [
        "# 公开随机抽签结果",
        "",
        "## 抽签规则",
        "",
        "先生成满足硬约束的优质方案池，公开 `scheme_pool.csv` 及其 SHA-256 摘要。现场公布随机数字串 `s` 后，计算 `R = int(SHA256(s|H), 16)`，其中 `H` 为方案池哈希；抽中编号 `q = R mod K + 1`。",
        "",
        "## 本次抽签记录",
        "",
        f"- 方案池规模 K：{len(ranked)}",
        f"- 方案池 SHA-256：`{digest}`",
        f"- 现场数字串 s：`{public_seed}`",
        f"- 二次哈希：`{draw.random_source.split('=')[1]}`",
        f"- 随机整数 R：{draw.public_random_number}",
        f"- 抽中编号 q：{draw.selected_index}",
        f"- 抽中方案：{selected['pool_id']}",
        f"- 来源候选方案：{selected['scheme_id']}",
        f"- TOPSIS 得分：{float(selected['topsis_score']):.6f}",
        "",
        "## 抽中分组",
        "",
        "| 小组 | 队伍 |",
        "|---|---|",
    ]
    for group, names in selected_groups.items():
        lines.append(f"| {group} | {'、'.join(names)} |")
    (output_dir / "final_draw_scheme.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (output_dir / "lottery_process.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return draw_record
