# udemy-crawler

A Python CLI that takes a Udemy quiz-series URL, walks every quiz in the series, and writes a single Word document containing one quiz per page plus a consolidated answer key on the final page.

## Stack

- **Python** 3.11+
- **curl_cffi** — Udemy REST API client. Udemy sits behind Cloudflare; plain `httpx`/`requests`/`Invoke-WebRequest` get a JS challenge instead of JSON. `curl_cffi` impersonates Chrome's TLS fingerprint and gets through.
- **python-docx** — Word document output
- **typer** — CLI framework
- **pytest** + **respx-style mocking via `pytest-httpserver` or `pytest-mock`** — `respx` is httpx-specific and doesn't intercept `curl_cffi`. See `.claude/rules/testing.md`.

## Authentication

Udemy auth in this project is **browser cookie-based**, not Bearer-token-based. (The exploration step on 2026-05-19 confirmed the captured browser traffic carries no `Authorization` header — all auth flows through cookies.)

- Cookies live at `~/Documents/.udemy/cookies.json` — a single JSON object mapping cookie name → value, exported from a logged-in Udemy tab.
- Required cookies: `cf_clearance`, `__cf_bm`, `access_token`, `dj_session_id`, `ud_user_jwt`, `client_id`, `csrftoken`, plus the `ud_cache_*` set.
- `cf_clearance` and `__cf_bm` are short-lived (hours). When the API returns HTML challenge pages, the user must re-export cookies. See `.claude/skills/extract-quiz/SKILL.md` for the full list and the re-export procedure.
- The crawler reads `cookies.json` once at process start and never logs or echoes any cookie value.

If `~/Documents/.udemy/cookies.json` is missing or unreadable, the tool fails fast with a one-line message and exit code 1.

## Output format

```
output/<course-slug>.docx
├── Quiz 1     (page 1)
├── Quiz 2     (page 2)
├── ...
└── Answer Key (final page)
```

Each quiz page: title heading, question(s) with lettered options. Final page: numbered list mapping each quiz to its correct option letter(s).

## Workflow

This project uses an **explore-then-codify** pattern because Udemy's quiz API shape is not pre-known.

1. **First run on a new course type:** `/explore-udemy <quiz-series-url>` — the `page-explorer` agent probes Udemy and writes the discovered endpoints, JSON shape, and pagination rules into `.claude/skills/extract-quiz/SKILL.md`.
2. **Subsequent runs:** `/crawl <quiz-series-url>` — uses the codified skill to walk the series and emit the `.docx`.

`/crawl` refuses to run while `extract-quiz/SKILL.md` is still a stub.

## Conventions

Modular rules live in `.claude/rules/`:

- [code-style.md](.claude/rules/code-style.md) — Python style, typing, module size
- [testing.md](.claude/rules/testing.md) — pytest + respx, fixture layout
- [crawler-conventions.md](.claude/rules/crawler-conventions.md) — rate limiting, auth handling, pagination rules

## Layout

```
udemy-crawler/
├── CLAUDE.md
├── .gitignore
├── .claude/           team scaffold (this folder is committed)
├── src/               crawler code (created in a follow-up after /explore-udemy)
├── tests/             pytest tests
└── output/            generated .docx files (gitignored)
```
