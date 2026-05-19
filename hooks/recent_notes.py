from __future__ import annotations

import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path


MAX_ITEMS = 6
OUTPUT_PATH = Path("assets/data/recent_notes.json")
SKIP_FILES = {"index.md"}


def on_config(config):
    docs_dir = Path(config["docs_dir"]).resolve()
    config_file = getattr(config, "config_file_path", None)
    project_dir = Path(config_file).resolve().parent if config_file else docs_dir.parent
    nav_files = _nav_file_set(config.get("nav", []))
    tracked_files = _git_tracked_file_set(project_dir, docs_dir)
    git_updates = _git_update_map(project_dir, docs_dir)
    notes = []

    for path in docs_dir.rglob("*.md"):
        rel_path = path.relative_to(docs_dir).as_posix()
        if path.name in SKIP_FILES or rel_path not in nav_files:
            continue

        title = _read_title(path)
        if not title:
            title = path.stem

        resolved_path = path.resolve()
        updated = git_updates.get(resolved_path)
        if updated is None:
            if resolved_path in tracked_files:
                continue
            updated = _mtime_updated_at(path)

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


def _git_update_map(project_dir: Path, docs_dir: Path) -> dict[Path, datetime]:
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
                "log",
                "--format=--DATE:%cI",
                "--name-only",
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
