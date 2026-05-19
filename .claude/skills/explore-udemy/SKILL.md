---
name: explore-udemy
description: Probe a Udemy quiz series to discover its API endpoints, JSON shape, and pagination rules, then codify the findings into the extract-quiz skill. Use when the user asks to explore/discover Udemy structure, or when extract-quiz/SKILL.md is still a stub.
---

# Skill: explore-udemy

This is the **bootstrap** skill. It runs the first time we touch a new course type. Its output is a populated `.claude/skills/extract-quiz/SKILL.md` — once that file exists in non-stub form, `/crawl` can run.

## Inputs

- A Udemy URL (course landing, curriculum item, or quiz).
- A token at `~/Documents/.udemy/` (file shape to be discovered in step 1).

## Steps

### 1. Token discovery

- List `~/Documents/.udemy/`. Identify the token file by content (a bearer token is typically a 40+ char alphanumeric string; an `access_token.json` object will contain it under `access_token`).
- Decide on the canonical helper path that the crawler will use, and record it in the skill output. Do **not** print the token value.

### 2. URL classification

Determine which kind of URL the user supplied:

| URL shape | Meaning |
| --- | --- |
| `udemy.com/course/<slug>/` | Course landing — need to derive `course_id` |
| `udemy.com/course/<slug>/learn/quiz/<quiz_id>` | Direct quiz |
| `udemy.com/course/<slug>/learn/lecture/<lecture_id>` | Curriculum item — quiz lives nearby |

Record how to derive `course_id` from each shape (the JSON in the page source, or the `/api-2.0/courses/?fields[course]=...` lookup).

### 3. Endpoint probing

Try these in order, using `WebFetch` with `Authorization: Bearer <token>`:

1. `GET /api-2.0/courses/{course_id}/cached-subscriber-curriculum-items/?page_size=100&fields[lecture]=title,object_index&fields[quiz]=title,object_index,type` — should return curriculum items including quizzes.
2. `GET /api-2.0/quizzes/{quiz_id}/assessments/?version=1` — quiz questions and options.
3. Variants to test if (2) is incomplete: append `&draft=false`, append `&fields[assessment]=@all`, try `?page_size=250`.

For each endpoint that works, record:
- The exact path and required query params.
- The path inside the response JSON to: quiz titles, question stems, option text, option ids, the correct option id/letter.

### 4. Pagination check

Find a course with >10 quizzes (or >10 curriculum items). Confirm the response contains `next` and `previous` link fields. Confirm following `next` returns the next page. Record the **link-following rule** (not page-number-based).

### 5. Answer source

Locate where the correct answer lives. Common patterns:

- `assessment.correct_response` — a string like `"a"` or a list of option ids.
- `assessment.prompt.explanation` — sometimes contains the correct answer plus rationale.
- If neither exists, the answer is only revealed by `POST /api-2.0/quizzes/{quiz_id}/assessment-answers/`. **Record this** — `/crawl` must not POST. We'd need a different approach.

### 6. Rate-limit observation

Note any `X-RateLimit-*` or `Retry-After` headers seen. Update `.claude/rules/crawler-conventions.md` only if observed limits are *tighter* than the conservative defaults already there.

### 7. Codify

Rewrite `.claude/skills/extract-quiz/SKILL.md` from scratch. Use this template:

```markdown
---
name: extract-quiz
description: Extract a single Udemy quiz (questions, options, correct answers) given a quiz_id and a bearer token.
---

# Skill: extract-quiz

## Endpoint

GET https://www.udemy.com/api-2.0/quizzes/{quiz_id}/assessments/?<params>

Headers: Authorization: Bearer <token>

## Response paths

- Question stem:  `results[].prompt.question`
- Options:        `results[].prompt.answers[]`  (each has `id`, `text`)
- Correct option: `results[].correct_response`  (string matching an option id)

## Listing all quizzes in a course

GET https://www.udemy.com/api-2.0/courses/{course_id}/cached-subscriber-curriculum-items/?page_size=100&fields[quiz]=title,type

Filter results where `_class == "quiz"`. Follow `next` until null.

## Pagination

Link-based. Follow the `next` URL verbatim. Do not compute page numbers.

## Course ID derivation

<recorded recipe here>
```

Replace the bracketed fields with what was actually observed.

### 8. Verification

- Re-read `extract-quiz/SKILL.md` and confirm `STUB —` no longer appears.
- Print a short summary to the user: endpoints found, answer field, pagination strategy.

## Failure modes

- 401 on every probe → token is stale; tell the user to refresh it.
- Endpoint (1) returns 200 but empty `results` → the course may be unpublished or the token's account doesn't own it; surface the response.
- No answer field found and no POST endpoint identified → stop, surface findings, ask the user how they want to proceed.
