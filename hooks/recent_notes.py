from __future__ import annotations

import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path


MAX_ITEMS = 6
OUTPUT_PATH = Path("assets/data/recent_notes.json")
SKIP_FILES = {"index.md"}
_PAGE_DATES: dict[str, dict[str, datetime]] = {}


def on_config(config):
    global _PAGE_DATES

    docs_dir = Path(config["docs_dir"]).resolve()
    config_file = getattr(config, "config_file_path", None)
    project_dir = Path(config_file).resolve().parent if config_file else docs_dir.parent
    nav_files = _nav_file_set(config.get("nav", []))
    tracked_files = _git_tracked_file_set(project_dir, docs_dir)
    git_updates = _git_date_map(project_dir, docs_dir)
    git_created = _git_date_map(project_dir, docs_dir, reverse=True)
    _PAGE_DATES = {}
    notes = []

    for path in docs_dir.rglob("*.md"):
        rel_path = path.relative_to(docs_dir).as_posix()
        resolved_path = path.resolve()
        updated = git_updates.get(resolved_path)
        created = git_created.get(resolved_path)
        if updated is None:
            if resolved_path in tracked_files:
                continue
            updated = _mtime_updated_at(path)
        if created is None:
            created = updated

        _PAGE_DATES[rel_path] = {"created": created, "updated": updated}

        if path.name in SKIP_FILES or rel_path not in nav_files:
            continue

        title = _read_title(path)
        if not title:
            title = path.stem

        notes.append(
            {
                "title": title,
                "url": _page_url(rel_path),
                "section": _section_name(rel_path),
                "updated": updated.isoformat(),
                "date": updated.strftime("%Y-%m-%d"),
            }
        )

    notes.sort(key=lambda item: item["updated"], reverse=True)

    output = docs_dir / OUTPUT_PATH
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(notes[:MAX_ITEMS], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return config


def on_page_markdown(markdown, page, config, files):
    src_path = getattr(page.file, "src_path", "").replace("\\", "/")
    if src_path == "index.md" or page.meta.get("page_dates") is False:
        return markdown

    dates = _PAGE_DATES.get(src_path)
    if not dates:
        return markdown

    created = dates["created"].strftime("%Y-%m-%d")
    updated = dates["updated"].strftime("%Y-%m-%d")
    return (
        markdown.rstrip()
        + f"""

<div class="article-dates" aria-label="文章日期">
  <span class="article-dates__item" title="发布时间" aria-label="发布时间">
    <svg class="article-dates__icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M19 3h-1V1h-2v2H8V1H6v2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2m0 16H5V8h14v11M7 10h5v5H7v-5Z"/></svg>
    <time datetime="{created}">{created}</time>
  </span>
  <span class="article-dates__item" title="更新时间" aria-label="更新时间">
    <svg class="article-dates__icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M21 10.12h-6.78l2.74-2.82c-2.73-2.7-7.15-2.8-9.88-.1-2.73 2.71-2.73 7.08 0 9.79s7.15 2.71 9.88 0c1.36-1.35 2.05-3.11 2.05-4.89h2c0 2.29-.88 4.58-2.64 6.33-3.51 3.48-9.21 3.48-12.72 0s-3.51-9.15 0-12.63 9.12-3.48 12.63 0L21 3v7.12Z"/></svg>
    <time datetime="{updated}">{updated}</time>
  </span>
</div>
"""
    )


def _nav_file_set(nav_items) -> set[str]:
    files = set()

    def visit(item):
        if isinstance(item, str):
            if item.endswith(".md"):
                files.add(item.replace("\\", "/"))
            return

        if isinstance(item, list):
            for child in item:
                visit(child)
            return

        if isinstance(item, dict):
            for child in item.values():
                visit(child)

    visit(nav_items)
    return files


def _git_tracked_file_set(project_dir: Path, docs_dir: Path) -> set[Path]:
    try:
        docs_arg = docs_dir.relative_to(project_dir).as_posix()
    except ValueError:
        docs_arg = str(docs_dir)

    try:
        result = subprocess.run(
            [
                "git",
                "-c",
                "core.quotepath=false",
                "ls-files",
                "--",
                docs_arg,
            ],
            cwd=project_dir,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return set()

    if result.returncode != 0:
        return set()

    return {
        (project_dir / line.strip()).resolve()
        for line in result.stdout.splitlines()
        if line.strip()
    }


def _read_title(path: Path) -> str:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""

    in_front_matter = text.startswith("---")
    for line in text.splitlines()[1 if in_front_matter else 0 :]:
        if in_front_matter and line.strip() == "---":
            in_front_matter = False
            continue
        if in_front_matter:
            continue

        match = re.match(r"^#\s+(.+?)\s*$", line)
        if match:
            return re.sub(r"\s*\{#.+?\}\s*$", "", match.group(1)).strip()
    return ""


def _git_date_map(
    project_dir: Path, docs_dir: Path, reverse: bool = False
) -> dict[Path, datetime]:
    try:
        docs_arg = docs_dir.relative_to(project_dir).as_posix()
    except ValueError:
        docs_arg = str(docs_dir)

    command = [
        "git",
        "-c",
        "core.quotepath=false",
        "log",
        "--format=--DATE:%cI",
        "--name-only",
    ]
    if reverse:
        command.append("--reverse")
    command.extend(["--", docs_arg])

    try:
        result = subprocess.run(
            command,
            cwd=project_dir,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return {}

    if result.returncode != 0:
        return {}

    updates = {}
    current_date = None
    for raw_line in result.stdout.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        if line.startswith("--DATE:"):
            try:
                current_date = datetime.fromisoformat(line[7:]).astimezone(timezone.utc)
            except ValueError:
                current_date = None
            continue

        if current_date is None:
            continue

        path = (project_dir / line).resolve()
        if docs_dir in path.parents and path.suffix == ".md" and path not in updates:
            updates[path] = current_date

    return updates


def _mtime_updated_at(path: Path) -> datetime:
    return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)


def _page_url(rel_path: str) -> str:
    if rel_path.endswith("/index.md"):
        page_path = rel_path[: -len("index.md")]
    else:
        page_path = rel_path[:-3] + "/"

    return page_path.replace("\\", "/")


def _section_name(rel_path: str) -> str:
    section = rel_path.split("/", 1)[0]
    names = {
        "ai": "AI",
        "control": "控制",
        "others": "其他",
        "robotic": "Robotics",
        "scholar": "Scholar",
        "zju-courses": "ZJU-Courses",
        "blog": "Blog",
    }
    return names.get(section, section)
