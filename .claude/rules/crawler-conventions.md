# Crawler conventions

The non-obvious rules. None of these are inferable from the code alone — codify them here so future contributors (and future Claude) don't relearn the hard way.

## Rate limits

- **Minimum 500 ms** between outbound requests to `udemy.com`.
- On HTTP 429: exponential backoff starting at 2s, doubling each retry, cap at 60s, give up after 5 attempts.
- Honour `Retry-After` headers when present — they override the backoff schedule.
- Never burst-parallel quiz requests. Sequential only.

## Authentication

- Token is read **once** at process start from `~/Documents/.udemy/`.
- The token never appears in logs, error messages, CLI flags, exception strings, or `__repr__` output. Wrap it in a `SecretStr`-style guard.
- If the API returns 401, the token is bad — exit non-zero with a clear message. Do not retry, do not re-read.
- If the API returns 403, the user does not own the resource — exit non-zero. We do not bypass paywalls.

## HTTP

- Always send a `User-Agent` that identifies this tool: `udemy-crawler/<version> (+local CLI)`.
- Set explicit `Accept: application/json, text/plain, */*` and `Accept-Language: en-US,en;q=0.9`.
- Connection timeout 10s, read timeout 30s.

## Pagination

- Follow the API's `next` link until it is `null`. Do **not** compute pages from `count` / `page_size` — Udemy occasionally returns inconsistent totals.
- Cap the walk at 500 quizzes to bound runaway crawls; emit a warning if hit and stop.

## Idempotency and resumption

- Treat each crawl as fresh. Do not implement caching/resume in the first version — the user can re-run.
- Output writes go to `output/<course-slug>.docx`; overwrite is fine and expected.

## What we do not do

- We do not scrape rendered HTML when an API endpoint exists. The DOM is a fallback only if the agent's exploration shows no JSON path to a given field.
- We do not submit quizzes or alter user state. All requests are GETs (with the one exception that the explore agent may verify an answer-revealing POST exists — it must not run it as part of `/crawl`).
- We do not parallelise. The latency cost is acceptable; the API anger is not.
