# Code style

## Python

- Target Python 3.11+.
- Format and lint with `ruff` (defaults). No bikeshedding on style — `ruff format` wins.
- **Type hints required** on every public function and method. Internal helpers may omit them when the type is obvious from a one-line return.
- Use `dataclasses` (or `pydantic` when validation is needed) for quiz/question models. No bare dicts in the public API of any module.
- Prefer `pathlib.Path` over `os.path`.
- `httpx` only — never mix in `requests` or `urllib`.

## Errors

- No bare `except:` and no `except Exception:` unless re-raised or logged with context.
- Domain errors (token missing, quiz not found, rate-limited beyond retry budget) get named exception classes in a single `errors.py` module. Catch the narrow type at the boundary, not in business logic.
- Fail fast on startup: missing token, unreadable token file, malformed URL → exit non-zero with a one-line message, no traceback.

## Modules

- Keep modules under ~300 lines. If it grows past that, split by responsibility (HTTP, parsing, document writing, CLI).
- One public class or one cohesive set of functions per module — not both.

## Comments

- Default to writing **no comments**. Names should carry the meaning.
- Write a comment only when the **why** is non-obvious: a workaround, a hidden constraint, a surprising invariant. Never describe the *what*.
- No comments referencing tasks, tickets, or "added for X" — those go in the commit message.
