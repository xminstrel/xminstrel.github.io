# Website performance

Build with Python 3.10+:

```sh
python -m pip install -r requirements.txt
python -m mkdocs build --clean
python -m unittest discover -s tests -v
```

## Images

`hooks/performance.py` generates WebP variants at widths up to 640, 1280 and 1920 px, without editing Markdown or source images. PNG diagrams use lossless WebP encoding; JPEG photographs use quality 82. Variants that exceed the original file size are discarded. The original remains available as a full-resolution candidate and through a new-tab link, unless an author already supplied a link. Animated images are preserved.

The first content image and the homepage avatar load eagerly. Subsequent images use native lazy loading. Intrinsic dimensions reserve layout space; existing author sizing and responsive sources are respected. The browser chooses a candidate via `srcset` and `sizes` according to the screen size and pixel density.

Generated images go into the build output only. `.cache/image-variants` stores content-addressed results between builds and is cached by GitHub Actions. The first build takes longer; subsequent builds reuse variants. Changes to the transformation require a new `CACHE_VERSION` in the hook.

## Navigation and runtime assets

The canonical site URL is `https://note.xminstrel.top/`. Material instant navigation preserves the search worker between pages. The random-note link uses native link navigation, so Material can intercept it. Test this against the configured origin or use `mkdocs serve`, which adjusts the development URL; serving production HTML at an unrelated origin does not exercise instant navigation correctly because its sitemap identifies production URLs.

Fonts are served locally with `font-display: swap`. KaTeX 0.19.0 is loaded once, only after visiting a page containing `.arithmatex`. Math rendering targets those elements and runs again on instant navigation. Giscus loads near the comment section and follows page and palette changes.

See `VENDOR.md` for asset versions, licenses and regeneration.

## Verification

Image regression tests cover Chinese/encoded paths, preserving originals, explicit links/sizing, custom responsive sources, remote images, escaped code samples and animation. Browser smoke testing should cover homepage → course tab → back → search → random note, formulas, directory folding, original-image links, deferred comments, light/dark palette, and a 390 px mobile viewport. Block external services to confirm that fonts and formulas work independently.

Existing build warnings about missing images in the mathematical-modeling draft and one heat-transfer exercise are unrelated source-content issues. Do not treat a successful build as confirmation that those missing originals have been recovered.

To rerun the browser smoke test with a separately installed Playwright and Google Chrome:

```sh
NODE_PATH=/path/to/playwright/node_modules node tests/browser-smoke.cjs /absolute/path/to/site
```

The test serves the specified build directly into an isolated browser context at the configured site origin. It stubs Giscus to verify mounting and blocks other external requests; it does not post comments or verify Giscus service availability. Screenshots and results are written under `/tmp`.

Measured in Chrome at 1440 × 1000, DPR 1, with empty cache and no scrolling: the materials note's initial image requests fell from 94 (33,751,909 bytes) to 6 (172,122 bytes), about 99.5% fewer image bytes. This measures initial image traffic, not real-world page-load time. The default image URLs across the full note total 15.5 MiB instead of 32.2 MiB; moments totals 5.3 MiB instead of 35.3 MiB. Actual transfers depend on scrolling, device pixel density, responsive image selection and cache state.
