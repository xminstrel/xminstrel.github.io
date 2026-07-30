from __future__ import annotations

import json
import re
import subprocess
import math
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


SITE_STATS_PATH = Path("assets/data/site_stats.json")
GARDEN_PATH = Path("assets/data/garden.json")
SKIP_FILES = {"index.md", "about_me.md"}
ARTICLE_MIN_WORDS = 20
_PAGE_DATES: dict[str, dict[str, datetime]] = {}
_PUBLIC_PAGE_SET: set[str] = set()


def on_config(config):
    global _PAGE_DATES, _PUBLIC_PAGE_SET

    docs_dir = Path(config["docs_dir"]).resolve()
    config_file = getattr(config, "config_file_path", None)
    project_dir = Path(config_file).resolve().parent if config_file else docs_dir.parent
    nav_files = _nav_file_set(config.get("nav", []))
    tracked_files = _git_tracked_file_set(project_dir, docs_dir)
    git_updates = _git_date_map(project_dir, docs_dir)
    git_created = _git_date_map(project_dir, docs_dir, reverse=True)
    _PAGE_DATES = {}
    _PUBLIC_PAGE_SET = set()
    raw_pages = {}
    notes = []

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
        raw_text = path.read_text(encoding="utf-8", errors="ignore")
        raw_pages[rel_path] = raw_text

        title = _read_title(path)
        if not title:
            title = path.stem

        word_count, reading_minutes = _reading_stats(raw_text)
        if word_count < ARTICLE_MIN_WORDS:
            continue

        tags = _page_tags(rel_path, raw_text)
        page_info = {
            "src": rel_path,
            "title": title,
            "url": _page_url(rel_path),
            "section": _section_name(rel_path),
            "tags": tags,
            "updated": updated.isoformat(),
            "date": updated.strftime("%Y-%m-%d"),
            "created": created.isoformat(),
            "words": word_count,
            "word_count": _format_word_count(word_count),
            "minutes": reading_minutes,
            "directory": str(Path(rel_path).parent).replace("\\", "/"),
        }
        if path.name not in SKIP_FILES and rel_path in nav_files:
            _PUBLIC_PAGE_SET.add(rel_path)
            notes.append(page_info)

    notes.sort(key=lambda item: item["updated"], reverse=True)
    garden = _build_garden_data(notes, raw_pages)

    public_word_count = sum(item["words"] for item in notes)
    site_stats = {
        "article_count": len(notes),
        "section_count": len({item["section"] for item in notes}),
        "total_words": public_word_count,
        "total_word_count": _format_word_count(public_word_count),
        "updated": max((item["updated"] for item in notes), default=""),
        "date": max((item["date"] for item in notes), default=""),
        "random_pages": notes,
        "pages": notes,
    }
    stats_output = docs_dir / SITE_STATS_PATH
    stats_output.parent.mkdir(parents=True, exist_ok=True)
    stats_output.write_text(
        json.dumps(site_stats, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    garden_output = docs_dir / GARDEN_PATH
    garden_output.parent.mkdir(parents=True, exist_ok=True)
    garden_output.write_text(
        json.dumps(garden, ensure_ascii=False, indent=2),
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

    updated = dates["updated"].strftime("%Y-%m-%d")
    word_count, reading_minutes = _reading_stats(markdown)
    stats_block = f"""
<div class="article-dates article-dates--top" aria-label="文章信息">
  <span class="article-dates__item" title="更新时间" aria-label="更新时间">
    <svg class="article-dates__icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M21 10.12h-6.78l2.74-2.82c-2.73-2.7-7.15-2.8-9.88-.1-2.73 2.71-2.73 7.08 0 9.79s7.15 2.71 9.88 0c1.36-1.35 2.05-3.11 2.05-4.89h2c0 2.29-.88 4.58-2.64 6.33-3.51 3.48-9.21 3.48-12.72 0s-3.51-9.15 0-12.63 9.12-3.48 12.63 0L21 3v7.12Z"/></svg>
    <time datetime="{updated}">更新于 {updated}</time>
  </span>
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
    relation_block = ""
    if src_path in _PUBLIC_PAGE_SET and page.meta.get("garden") is not False:
        relation_block = f"""

<section class="garden-relations" data-page-relations data-page-src="{src_path}">
  <h2>关联笔记</h2>
  <div class="garden-relations__body">
    <span class="home-update-card home-update-card--empty">正在整理关联笔记...</span>
  </div>
</section>
"""

    return _insert_after_title(markdown.rstrip(), stats_block).rstrip() + relation_block


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


def _build_garden_data(public_pages: list[dict], raw_pages: dict[str, str]) -> dict:
    public_src = {page["src"] for page in public_pages}
    title_index = _title_index(public_pages)
    outgoing: dict[str, list[str]] = {}
    backlinks: dict[str, set[str]] = {page["src"]: set() for page in public_pages}

    for page in public_pages:
        src = page["src"]
        targets = _resolve_page_links(src, raw_pages.get(src, ""), public_src, title_index)
        outgoing[src] = targets
        for target in targets:
            backlinks.setdefault(target, set()).add(src)

    pages_by_src = {page["src"]: page for page in public_pages}
    tags: dict[str, list[str]] = defaultdict(list)

    for page in public_pages:
        for tag in page.get("tags", []):
            tags[tag].append(page["src"])

    enriched_pages = []
    for page in public_pages:
        src = page["src"]
        copy = dict(page)
        copy["outgoing"] = [_page_ref(pages_by_src[target]) for target in outgoing.get(src, [])]
        copy["backlinks"] = [
            _page_ref(pages_by_src[source])
            for source in sorted(backlinks.get(src, set()), key=lambda item: pages_by_src[item]["title"])
        ]
        copy["related"] = [
            _page_ref(pages_by_src[target])
            for target in _related_pages(src, public_pages, outgoing, backlinks)
        ]
        enriched_pages.append(copy)

    tag_items = []
    for tag, srcs in tags.items():
        tag_pages = [pages_by_src[src] for src in srcs if src in pages_by_src]
        tag_pages.sort(key=lambda item: item["updated"], reverse=True)
        tag_items.append(
            {
                "name": tag,
                "count": len(tag_pages),
                "pages": [_page_ref(page) for page in tag_pages],
            }
        )

    tag_items.sort(key=lambda item: (-item["count"], item["name"]))
    sections = []
    for section, items in _group_by(enriched_pages, "section").items():
        sections.append({"name": section, "count": len(items)})
    sections.sort(key=lambda item: (-item["count"], item["name"]))

    enriched_pages.sort(key=lambda item: item["updated"], reverse=True)
    return {
        "pages": enriched_pages,
        "tags": tag_items,
        "sections": sections,
    }


def _page_ref(page: dict) -> dict:
    return {
        "src": page["src"],
        "title": page["title"],
        "url": page["url"],
        "section": page["section"],
        "date": page["date"],
        "updated": page["updated"],
        "tags": page.get("tags", []),
        "word_count": page.get("word_count", ""),
        "minutes": page.get("minutes", 1),
    }


def _related_pages(
    src: str,
    public_pages: list[dict],
    outgoing: dict[str, list[str]],
    backlinks: dict[str, set[str]],
) -> list[str]:
    page_by_src = {page["src"]: page for page in public_pages}
    current = page_by_src[src]
    current_tags = set(current.get("tags", [])) - {current.get("section")}
    explicit = set(outgoing.get(src, [])) | backlinks.get(src, set())
    candidates = []

    for page in public_pages:
        target = page["src"]
        if target == src or target in explicit:
            continue

        candidate_tags = set(page.get("tags", [])) - {page.get("section")}
        shared = current_tags & candidate_tags
        if not shared:
            continue

        candidates.append((len(shared), page["updated"], target))

    candidates.sort(reverse=True)
    return [target for _, __, target in candidates[:4]]


def _resolve_page_links(
    src: str, markdown: str, public_src: set[str], title_index: dict[str, list[str]]
) -> list[str]:
    candidates = []

    for match in re.findall(r"\[\[([^\]]+?)]]", markdown):
        candidates.append(match.split("|", 1)[0].split("#", 1)[0].strip())

    for match in re.findall(r"(?<!!)\[[^\]]+]\(([^)]+)\)", markdown):
        href = match.split("#", 1)[0].split("?", 1)[0].strip()
        if not href or re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", href):
            continue
        if href.startswith("#") or href.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".svg", ".pdf", ".zip")):
            continue
        candidates.append(href)

    resolved = []
    for candidate in candidates:
        target = _resolve_link_target(src, candidate, public_src, title_index)
        if target and target != src and target not in resolved:
            resolved.append(target)
    return resolved


def _resolve_link_target(
    src: str, candidate: str, public_src: set[str], title_index: dict[str, list[str]]
) -> str | None:
    normalized = candidate.replace("\\", "/").strip()
    if not normalized:
        return None

    if normalized in public_src:
        return normalized

    if normalized.endswith("/"):
        index_target = normalized + "index.md"
        if index_target in public_src:
            return index_target

    if not normalized.endswith(".md"):
        md_target = normalized + ".md"
        if md_target in public_src:
            return md_target
    elif normalized in public_src:
        return normalized

    relative = (Path(src).parent / normalized).as_posix()
    if relative in public_src:
        return relative
    if not relative.endswith(".md") and f"{relative}.md" in public_src:
        return f"{relative}.md"

    key = Path(normalized).stem if normalized.endswith(".md") else normalized
    matches = title_index.get(key) or title_index.get(Path(key).name)
    if matches:
        return matches[0]

    return None


def _title_index(public_pages: list[dict]) -> dict[str, list[str]]:
    index: dict[str, list[str]] = defaultdict(list)
    for page in public_pages:
        src = page["src"]
        index[page["title"]].append(src)
        index[Path(src).stem].append(src)
        index[src.removesuffix(".md")].append(src)

    return index


def _page_tags(rel_path: str, markdown: str) -> list[str]:
    tags = []
    explicit = _front_matter_tags(markdown)
    for tag in explicit:
        _append_unique(tags, tag)

    _append_unique(tags, _section_name(rel_path))
    parent = Path(rel_path).parent
    parts = [part for part in parent.parts if part not in (".", "")]
    if len(parts) >= 2:
        _append_unique(tags, parts[1])

    return tags


def _front_matter_tags(markdown: str) -> list[str]:
    if not markdown.startswith("---"):
        return []

    lines = markdown.splitlines()
    end = None
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end = index
            break

    if end is None:
        return []

    tags = []
    in_tags = False
    for line in lines[1:end]:
        stripped = line.strip()
        if not stripped:
            continue

        if re.match(r"^[A-Za-z_-]+:", stripped) and not stripped.startswith("tags:"):
            in_tags = False

        if stripped.startswith("tags:"):
            in_tags = True
            value = stripped.split(":", 1)[1].strip()
            if value.startswith("[") and value.endswith("]"):
                for item in value[1:-1].split(","):
                    _append_unique(tags, item.strip().strip("\"'"))
            elif value:
                _append_unique(tags, value.strip("\"'"))
            continue

        if in_tags and stripped.startswith("-"):
            _append_unique(tags, stripped[1:].strip().strip("\"'"))

    return tags


def _append_unique(items: list[str], value: str | None):
    if not value:
        return
    value = str(value).strip()
    if value and value not in items:
        items.append(value)


def _group_by(items: list[dict], key: str) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for item in items:
        grouped[item.get(key, "未分类")].append(item)
    return grouped


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
        "resources": "Resources",
        "robotic": "Robotics",
        "scholar": "Scholar",
        "zju-courses": "ZJU-Courses",
    }
    return names.get(section, section)
