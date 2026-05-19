# Testing

## Framework

- `pytest` for everything.
- HTTP is mocked at the transport boundary — `pytest-httpserver` (runs a local HTTP server that `curl_cffi` hits exactly like the real Udemy) is the recommended approach. **Do not use `respx`** (httpx-specific; we're on `curl_cffi`) or `responses` (`requests`-specific). Bare `unittest.mock` of HTTP calls is also out — mock at the wire, not the function.

## Layout

```
tests/
├── conftest.py           shared fixtures (mock token dir, sample course slug)
├── fixtures/             recorded JSON responses (one file per Udemy endpoint)
├── test_<module>.py      one test file per src/ module
└── integration/
    └── test_live.py      opt-in, skipped unless UDEMY_TOKEN env var is set
```

## Conventions

- **No network in unit tests.** Every test that would hit Udemy uses `respx` to serve the captured JSON from `tests/fixtures/`.
- Recording fixtures is a manual step — capture once during `/explore-udemy`, redact PII, commit.
- One assertion per test where practical. Use `pytest.mark.parametrize` for table-driven cases (e.g. answer-letter mapping).
- Fail-fast: tests should error within milliseconds. If a test takes >1s, it belongs in `integration/`.

## Coverage expectations

- Unit-test the pure functions: option-letter mapping, pagination follow-next loop, doc-writer assembly.
- Integration test (skipped by default) hits one real quiz against the user's account to catch API drift. Run via `UDEMY_TOKEN=... pytest tests/integration/`.
