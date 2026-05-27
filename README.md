# udemy-crawler

A Python CLI that walks a Udemy quiz series via the REST API and emits a Word document — one question per page, with a consolidated answer key at the end. Built for owners of practice-test courses who want an offline, printable, searchable copy of the material they paid for.

## Status

Working end-to-end. Used in anger on a 5-quiz, 500-question practice-test course; produced two 125 KB `.docx` files with no manual intervention.

## How it works

1. You hand the CLI a Udemy URL (course landing, curriculum item, or quiz page).
2. It lists every quiz in the series via `/api-2.0/courses/<id>/cached-subscriber-curriculum-items/`, then walks `/api-2.0/quizzes/<id>/assessments/` to pull each question's stem, options, and correct-answer letter.
3. It dumps the structured result to JSON, then a small `python-docx` script lays out the Word document.

Two output variants:

| File | Layout |
| --- | --- |
| `output/<slug>.docx` | Plain. One question per page, answer key at the end. |
| `output/<slug>-highlighted.docx` | Same layout but the correct option on every question is rendered with a yellow highlight + bold for at-a-glance review. |

For architecture, ADRs, and risks, see [`docs/arc42.md`](docs/arc42.md).

## Requirements

- Python 3.11+ (developed against 3.14)
- `curl_cffi` (Chrome TLS impersonation — needed to clear Cloudflare)
- `python-docx`

```bash
pip install curl_cffi python-docx
```

## Authentication

Udemy is fronted by Cloudflare, so the tool uses your real browser session rather than a Bearer token. You need two files in `~/Documents/.udemy/`:

| File | Contents |
| --- | --- |
| `cookies.json` | Flat JSON object `{name: value, ...}` from a logged-in Udemy tab. Must include `cf_clearance`, `__cf_bm`, `access_token`, `dj_session_id`, `ud_user_jwt`, `csrftoken`, and the `ud_cache_*` set. |
| `headers.json` | Flat JSON object of the non-cookie request headers Udemy expects (`x-udemy-cache-*`, `sec-ch-ua-*`, `accept`, `x-requested-with`, …). |

The `cf_clearance` and `__cf_bm` cookies expire on the order of hours. When the API starts returning HTML challenge pages instead of JSON, re-export them from your browser — the crawler will raise a `CloudflareChallenge` exception with a clear message.

### How to capture them

1. Open a logged-in Udemy tab and open DevTools → Network.
2. Trigger a quiz fetch in the UI.
3. Right-click any `/api-2.0/...` request → **Copy → Copy as Node fetch** (or PowerShell — either works).
4. Parse the `cookie:` header into `cookies.json`; copy the remaining request headers into `headers.json`.

A throwaway parse script is included at `.claude/skills/explore-udemy/.scratch/persist_auth.py` (gitignored). Promoting it to a first-class `refresh-auth` command is open work — see [arc42 §11](docs/arc42.md#11-risks-and-technical-debt).

## Usage

### Direct Python invocation

```bash
# 1. Crawl: walk the series, dump structured JSON
PYTHONPATH=src python -m udemy_crawler.cli \
    "https://www.udemy.com/course/<slug>/learn/quiz/<id>/test"

# 2. Build the plain docx
python scripts/_build_doc.py \
    "output/<slug>-quizzes.json" \
    "output/<slug>.docx"

# 3. Build the highlighted docx
python scripts/_build_doc_highlighted.py \
    "output/<slug>-quizzes.json" \
    "output/<slug>-highlighted.docx"
```

### Via Claude Code

If you have Claude Code with this repo open, the orchestration is wired through slash commands:

- `/explore-udemy <url>` — first-time bootstrap. Probes the API and codifies findings into `.claude/skills/extract-quiz/SKILL.md`. Run once per new course shape.
- `/crawl <url>` — full pipeline: walk the series, extract every quiz, hand off to the doc-writer agent, produce both `.docx` variants.

## Project layout

```
udemy-crawler/
├── CLAUDE.md                         project brief (for Claude Code)
├── README.md                         this file
├── docs/
│   └── arc42.md                      architecture documentation
├── .claude/
│   ├── agents/                       page-explorer, quiz-extractor, doc-writer
│   ├── commands/                     /explore-udemy, /crawl
│   ├── rules/                        code style, testing, crawler conventions
│   └── skills/                       explore-udemy, extract-quiz, generate-word-doc
├── src/udemy_crawler/                Python package — 8 modules
│   ├── __init__.py   errors.py   models.py
│   ├── auth.py       client.py   extract.py
│   └── cli.py        text.py
├── scripts/
│   ├── _build_doc.py                 plain docx assembly
│   └── _build_doc_highlighted.py     highlighted docx assembly
└── output/                           generated artefacts (gitignored)
```

## Limitations

- **Single-account.** No multi-tenant support; one user's cookies at a time.
- **Browser cookies expire.** No automatic refresh. Re-export when calls start returning HTML.
- **No resume.** A failed crawl mid-series re-fetches from quiz 1 on the next attempt. Per the [crawler conventions](.claude/rules/crawler-conventions.md), caching/resume was deliberately deferred to v2.
- **No parallelism.** One request at a time, 500 ms apart. Udemy's API is touchy; the latency cost is small.
- **Untested on multi-answer questions.** The data model supports them (`correct_response` is a list), but the course used during exploration was all single-answer.

See [arc42 §11](docs/arc42.md#11-risks-and-technical-debt) for the full risk register.

## Ethics

This tool walks the public Udemy REST API as the authenticated owner of a course. It does not scrape rendered HTML when an API exists, submit quizzes, modify account state, or POST to `assessment-answers/` (which would reveal answers via a side-effect endpoint). All answer letters come from the GET response Udemy returns to a subscribed learner.

Use it on courses you own, for your own study. The generated `.docx` redistributes Udemy course content and should not be shared.
