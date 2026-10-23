# Local runtime assets

- KaTeX **0.19.0**: upstream distribution and MIT license, including its fonts.
- LXGW WenKai Screen **1.1.0**: the complete Screen family, split by Unicode range. The unused Screen R family is omitted. See the bundled licenses.
- JetBrains Mono **5.2.8** (@fontsource package): Latin normal 400/700 WOFF2 and SIL Open Font License.
- Noto Serif SC: Google Fonts source, subset to the text currently in `docs/`, plus ASCII and punctuation, for decorative headings. Other characters fall back to the existing system serif stack. SIL Open Font License is included.

All runtime font declarations use `font-display: swap`. Fonts and math rendering need no third-party network requests. The comment widget is still provided by Giscus and is loaded only near the comment section.

To refresh these assets, install `fonttools` and `brotli` into a development environment, then run `python scripts/vendor_assets.py`. This is an explicit maintenance step, not part of a normal site build. Regenerate the Noto subset if headings need characters it does not contain.
