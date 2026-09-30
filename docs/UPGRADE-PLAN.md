# Upgrade plan — book-grant-data

Current state: **7/10** (pass 1: 5 -> 7; pass 2: 7, consumer-facing CLI fix). Offline contract, adapters and CLI are tested and linted in CI; live capture, source permission and consumers remain unverified by design.

## Backlog

- P0: Push this branch and confirm the new GitHub Actions `CI` workflow is green on both Python versions.
- P1: Strengthen drift markers for `sba-small-business-grants` — their `required_markers` are only fragments of the title, so a challenge or error page that repeats the title would pass. Pick body phrases from a captured page (needs a reviewed live capture; not done offline).
- P1: Replace the copy of `cli.py`/`capture.py` scaffolding shared by the sibling `book-*-data` repos with the shared runtime package once it is independently installable (README gate 3).
- P1: ZEVI 2 deadline (2026-09-16) has passed; add the next reviewed competition as a new source record ID rather than editing history.
- P2: `depa` directory stays status `unknown`; add a round-specific parser only when an exact window is published.
- P2: Add a live-capture smoke job only behind an explicit manual trigger and reviewed source permission (never on push).

## Done in this pass (pass 1)

- Added `.github/workflows/ci.yml`: `ruff check`, `pytest` and an offline CLI smoke (`contract`, `validate demo.json`, `demo --open-only`) on Python 3.10 and 3.13.
- Added `[project.optional-dependencies] dev` (pytest, pinned ruff), `[tool.ruff]` and `[tool.pytest.ini_options]` to `pyproject.toml`; fixed import-order lint.
- Added `tests/test_registry.py`: `sources.json` ↔ packaged `source*.json` consistency (product, domain, category in contract, https URLs, interval), source-ID selector rejects traversal/unknown IDs, every marker-driven adapter normalizes a synthetic page into a valid live record and rejects a challenge page, JSON adapters reject non-object payloads, CLI `validate` exit codes do not echo input.
- Removed dead GitHub-Education and Chevening template branches; unknown sources now fail closed (`unknown grant source`).
- GOV.UK Content API adapter rejects non-object JSON with `ValueError`.
- README source list now names all seven sources; stale GitHub/Chevening attribution removed.

## Done in this pass (pass 2)

- `contract --version {v1,v2}` (default v1, output unchanged) prints `schema-v2.json`, the
  contract every captured record uses; before, consumers of live data could only get v1.
  Unknown versions exit 2. Registry test, CI smoke and README updated (same change as the
  sibling scholarship/freebie/grant/benefit CLIs).
- Weak drift markers left unchanged: stronger phrases need a reviewed live capture.
- Drift guard: the HTML text extractor now also ignores `<noscript>` and `<svg>` (matching
  the sibling creator/deal/learning/mobility/paid-study/partnership/startup adapters), so
  markers hidden there cannot pass a challenge page; `tests/test_text_extraction.py`.

## Done in this pass (pass 3)

- Score: 7 -> 7.5.
- ZEVI "<date> <h:mm>am UK time" cutoff is parsed without `strptime(%B/%p)` (host-locale dependent) and a naive `checked_at` now raises ValueError instead of TypeError; tests cover BST/GMT, noon/midnight, the repeated October hour and offset boundaries. Added `tzdata; sys_platform == 'win32'` so `ZoneInfo('Europe/London')` works on Windows.
- Shared `cli.py` (same edit in all 13 sibling copies): `validate` now rejects NaN, ±Infinity and overflowing literals such as `1e400` (Python's json turns them into non-finite floats that JSON Schema `number` accepted); `timestamp` normalises fractional seconds so Python 3.10 accepts the same RFC3339 values as 3.11+ (it rejected e.g. `.1Z`) and only ASCII digits match; a trailing-dot `example.org.` host can no longer be claimed `live`.
- `tests/test_shared_cli.py` (byte-identical in all 13 repos) pins this repo's `cli.py` sha256 (three variants: base, +`contract --version`, +benefit availability) so a one-repo edit fails CI, and covers the fixes above across UTC/+07:00/-04:00 offsets. To change `cli.py`: edit every copy of the variant, then update `CLI_SHA256` in all 13 copies of the test.
- Not done (needs a reviewed live capture, so left blocked): stronger drift markers and any page-phrase extraction; no page phrases were invented.

## Done in this pass (pass 4: edge cases)

- Shared `cli.py` (all 13 copies, pins updated in `tests/test_shared_cli.py`):
  - `validate` accepted `" "` or a lone U+200B/BOM/soft hyphen as `id`,
    `title`, `provider` or `eligibility_text` (schema `minLength: 1` counts
    invisible characters); these are now rejected as blank.
  - Record ids that differ only by invisible characters or surrounding
    whitespace (`"x"` vs `"​x "`) are now reported as duplicates.
  - `demo --query` compared raw `casefold()` strings, so Thai SARA AM (`ำ`)
    did not match NIKHAHIT + SARA AA (either mark order), Thai digits did not
    match ASCII (`๒๕๖๙` vs `2569`), and full-width Latin (`ＵＫ`) or a stray
    zero-width space never matched; both sides are now NFKC-folded.
  - Verified: new `TextNormalisationTest` (all cases fail on the old code);
    full suite on Python 3.10 and 3.11; ruff 0.15.8 + 0.16.9.
