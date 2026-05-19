from __future__ import annotations

import json
import re
import subprocess
import math
from datetime import datetime, timezone
from pathlib import Path


MAX_ITEMS = 6
OUTPUT_PATH = Path("assets/data/recent_notes.json")
SITE_STATS_PATH = Path("assets/data/site_stats.json")
SKIP_FILES = {"index.md"}
ARTICLE_MIN_WORDS = 20
_PAGE_DATES: dict[str, dict[str, datetime]] = {}
_PAGE_INFO: dict[str, dict] = {}


def on_config(config):
    global _PAGE_DATES, _PAGE_INFO

    docs_dir = Path(config["docs_dir"]).resolve()
    config_file = getattr(config, "config_file_path", None)
    project_dir = Path(config_file).resolve().parent if config_file else docs_dir.parent
    nav_files = _nav_file_set(config.get("nav", []))
    tracked_files = _git_tracked_file_set(project_dir, docs_dir)
    git_updates = _git_date_map(project_dir, docs_dir)
    git_created = _git_date_map(project_dir, docs_dir, reverse=True)
    _PAGE_DATES = {}
    _PAGE_INFO = {}
    notes = []
    pages = []

    for path in docs_dir.rglob("*.md"):
        rel_path = path.relative_to(docs_dir).as_posix()
        if rel_path == "index.md":
            continue

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

        title = _read_title(path)
        if not title:
            title = path.stem

        word_count, reading_minutes = _reading_stats(
            path.read_text(encoding="utf-8", errors="ignore")
        )
        if word_count < ARTICLE_MIN_WORDS:
            continue

        page_info = {
            "title": title,
            "url": _page_url(rel_path),
            "section": _section_name(rel_path),
            "updated": updated.isoformat(),
            "date": updated.strftime("%Y-%m-%d"),
            "created": created.isoformat(),
            "words": word_count,
            "word_count": _format_word_count(word_count),
            "minutes": reading_minutes,
            "directory": str(Path(rel_path).parent).replace("\\", "/"),
        }
        _PAGE_INFO[rel_path] = page_info
        pages.append(page_info)

        if path.name not in SKIP_FILES and rel_path in nav_files:
            notes.append(page_info)

    notes.sort(key=lambda item: item["updated"], reverse=True)

    output = docs_dir / OUTPUT_PATH
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(notes[:MAX_ITEMS], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    pages.sort(key=lambda item: item["title"])
    site_stats = {
        "article_count": len(pages),
        "section_count": len({item["section"] for item in pages}),
        "total_words": sum(item["words"] for item in pages),
        "total_word_count": _format_word_count(sum(item["words"] for item in pages)),
        "updated": max((item["updated"] for item in pages), default=""),
        "date": max((item["date"] for item in pages), default=""),
        "random_pages": notes,
        "pages": pages,
    }
    stats_output = docs_dir / SITE_STATS_PATH
    stats_output.parent.mkdir(parents=True, exist_ok=True)
    stats_output.write_text(
        json.dumps(site_stats, ensure_ascii=False, indent=2),
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
    word_count, reading_minutes = _reading_stats(markdown)
    stats_block = f"""
<div class="article-dates article-dates--top" aria-label="文章概览">
  <span class="article-dates__item" title="全文字数" aria-label="全文字数">
    <svg class="article-dates__icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M5 4v3h5.5v12h3V7H19V4H5m0 8h3v7h3v-7h3V9H5v3Z"/></svg>
    <span>约 {_format_word_count(word_count)}</span>
  </span>
  <span class="article-dates__item" title="阅读时间" aria-label="阅读时间">
    <svg class="article-dates__icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 20a8 8 0 1 0 0-16 8 8 0 0 0 0 16m0-18a10 10 0 1 1 0 20 10 10 0 0 1 0-20m.5 5v5.25l4.5 2.67-.75 1.23L11 13V7h1.5Z"/></svg>
    <span>约 {reading_minutes} 分钟</span>
  </span>
</div>
"""
    dates_block = f"""

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
    return _insert_after_title(markdown.rstrip(), stats_block).rstrip() + dates_block


def _reading_stats(markdown: str) -> tuple[int, int]:
    text = _strip_front_matter(markdown)
    text = re.sub(r"```.*?```", " ", text, flags=re.DOTALL)
    text = re.sub(r"`[^`]*`", " ", text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"!\[[^\]]*]\([^)]*\)", " ", text)
    text = re.sub(r"\[([^\]]+)]\([^)]*\)", r"\1", text)
    text = re.sub(r"^[#>\-\*\+\s]+", " ", text, flags=re.MULTILINE)
    text = re.sub(r"[*_~=`|\\{}\[\]()<>\-]+", " ", text)

    chinese_chars = re.findall(r"[\u4e00-\u9fff]", text)
    latin_words = re.findall(r"[A-Za-z0-9]+(?:[-'][A-Za-z0-9]+)?", text)
    word_count = len(chinese_chars) + len(latin_words)
    reading_minutes = max(1, math.ceil(word_count / 400))
    return word_count, reading_minutes


def _insert_after_title(markdown: str, block: str) -> str:
    lines = markdown.splitlines()
    insert_after = None
    search_start = 0

    if lines and lines[0].strip() == "---":
        for index, line in enumerate(lines[1:], start=1):
            if line.strip() == "---":
                search_start = index + 1
                break

    for index in range(search_start, len(lines)):
        if re.match(r"^#\s+", lines[index]):
            insert_after = index + 1
            break

    if insert_after is None:
        insert_after = search_start

    before = "\n".join(lines[:insert_after]).rstrip()
    after = "\n".join(lines[insert_after:]).lstrip("\n")
    return f"{before}\n\n{block.strip()}\n\n{after}".rstrip()


def _format_word_count(word_count: int) -> str:
    if word_count >= 10000:
        return f"{word_count / 10000:.1f} 万字"
    return f"{word_count:,} 字"


def _strip_front_matter(markdown: str) -> str:
    if not markdown.startswith("---"):
        return markdown

    parts = markdown.split("---", 2)
    if len(parts) == 3:
        return parts[2]
    return markdown


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
