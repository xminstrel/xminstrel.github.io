"""Generate cached responsive images without changing Markdown or original assets."""
from __future__ import annotations

import hashlib
import html
import logging
import posixpath
import shutil
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import quote, unquote, urljoin, urlsplit

from PIL import Image, ImageOps

log = logging.getLogger("mkdocs.hooks.performance")
IMAGE_WIDTHS = (640, 1280, 1920)
CACHE_VERSION = "webp-v1"
_ASSETS = {}
_VARIANTS = {}


def on_files(files, config):
    _ASSETS.clear()
    _VARIANTS.clear()
    _ASSETS.update({file.dest_uri: file for file in files if file.abs_src_path})
    return files


def _variants(source: Path, config):
    """Keep diagrams lossless; resize photos and encode them at reading quality."""
    if source in _VARIANTS:
        return _VARIANTS[source]
    with Image.open(source) as image:
        if getattr(image, "is_animated", False):
            _VARIANTS[source] = None
            return None
        image = ImageOps.exif_transpose(image)
        width, height = image.size
        if width * height > 60_000_000:
            return None
        lossless = source.suffix.lower() == ".png"
        digest = hashlib.sha256(source.read_bytes() + CACHE_VERSION.encode()).hexdigest()[:24]
        cache = Path(config["config_file_path"]).parent / ".cache/image-variants"
        output = Path(config["site_dir"])
        cache.mkdir(parents=True, exist_ok=True)
        sizes = sorted({min(width, size) for size in IMAGE_WIDTHS})
        variants = []
        for size in sizes:
            name = f"{digest}-{size}.webp"
            cached = cache / name
            if not cached.exists():
                resized = image.convert("RGBA" if "A" in image.getbands() or "transparency" in image.info else "RGB")
                if size < width:
                    resized = resized.resize((size, max(1, round(height * size / width))), Image.Resampling.LANCZOS)
                resized.save(cached, "WEBP", lossless=lossless, quality=82, method=4)
            # A WebP that is larger than the original would waste bandwidth.
            if cached.stat().st_size >= source.stat().st_size:
                continue
            uri = f"assets/optimized/{name}"
            target = output / uri
            target.parent.mkdir(parents=True, exist_ok=True)
            if not target.exists():
                shutil.copyfile(cached, target)
            variants.append((size, uri))
        result = (width, height, variants)
        _VARIANTS[source] = result
        return result


class _Images(HTMLParser):
    def __init__(self, content, page, config):
        super().__init__(convert_charrefs=False)
        self.content, self.page, self.config = content, page, config
        self.offsets = [0]
        for line in content.splitlines(keepends=True):
            self.offsets.append(self.offsets[-1] + len(line))
        self.changes = []
        self.parents = []
        self.count = 0

    def handle_starttag(self, tag, attrs):
        if tag == "img":
            self.replace_image(dict(attrs))
        elif tag not in {"area", "base", "br", "col", "embed", "hr", "input", "link", "meta", "param", "source", "track", "wbr"}:
            self.parents.append(tag)

    def handle_startendtag(self, tag, attrs):
        if tag == "img":
            self.replace_image(dict(attrs))

    def handle_endtag(self, tag):
        if tag in self.parents:
            self.parents = self.parents[:len(self.parents) - 1 - self.parents[::-1].index(tag)]

    def replace_image(self, attrs):
        if {"twemoji", "emoji"}.intersection(attrs.get("class", "").split()):
            return
        original = attrs.get("src", "")
        parsed = urlsplit(original)
        avatar = "home-avatar" in attrs.get("class", "").split()
        self.count += 1
        attrs.setdefault("loading", "eager" if avatar or self.count == 1 else "lazy")
        attrs.setdefault("decoding", "async")
        if avatar:
            attrs.setdefault("fetchpriority", "high")
        # Remote images retain their URL, but still get native lazy loading.
        uri = unquote(urlsplit(urljoin(self.page.file.url, parsed.path)).path).lstrip("/")
        file = _ASSETS.get(uri) if not parsed.scheme and not parsed.netloc else None
        optimized = False
        if file and Path(file.abs_src_path).suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}:
            source = Path(file.abs_src_path)
            try:
                result = _variants(source, self.config)
                if result:
                    width, height, variants = result
                    # Preserve explicit author sizing, otherwise reserve the intrinsic ratio.
                    if "width" not in attrs and "height" not in attrs:
                        attrs.update(width=str(width), height=str(height))
                    if variants and not avatar and "srcset" not in attrs:
                        # Retain a full-resolution choice when the original encodes
                        # more efficiently than WebP at its native width.
                        if not any(size == width for size, _ in variants):
                            variants = sorted([*variants, (width, file.dest_uri)])
                        def relative(target):
                            base = posixpath.dirname(self.page.file.url) if not self.page.file.url.endswith("/") else self.page.file.url
                            return quote(posixpath.relpath(target, base or "."), safe="/-._~")
                        default = next((v for v in variants if v[0] >= min(width, 1280)), variants[-1])
                        attrs["src"] = relative(default[1])
                        attrs["srcset"] = ", ".join(f"{relative(path)} {size}w" for size, path in variants)
                        attrs.setdefault("sizes", "(max-width: 800px) 100vw, 980px" if any(c in attrs.get("class", "").split() for c in ("img-wide", "img-full", "img-natural")) else "(max-width: 800px) 100vw, 760px")
                        optimized = True
            except (OSError, ValueError) as error:
                log.warning("Cannot optimize image %s: %s", source, error)
        tag = "<img " + " ".join(key if value is None else f'{key}="{html.escape(value, quote=True)}"' for key, value in attrs.items()) + ">"
        if optimized and not any(parent in {"a", "button", "picture"} for parent in self.parents):
            tag = f'<a href="{html.escape(original, quote=True)}" target="_blank" rel="noopener" data-no-instant title="查看原图">{tag}</a>'
        line, col = self.getpos()
        start = self.offsets[line - 1] + col
        self.changes.append((start, start + len(self.get_starttag_text()), tag))


def on_page_content(html, page, config, files):
    parser = _Images(html, page, config)
    parser.feed(html)
    for start, end, replacement in reversed(parser.changes):
        html = html[:start] + replacement + html[end:]
    return html
