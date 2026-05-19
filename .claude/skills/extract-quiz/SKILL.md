---
name: extract-quiz
description: Extract a single Udemy quiz (questions, options, correct answers, explanations) given a quiz_id and an authenticated browser cookie session. Populated 2026-05-19 from a real practice-test course (course identifiers redacted).
---

# Skill: extract-quiz

## Authentication

Udemy sits behind Cloudflare. Plain HTTP clients (`httpx`, `Invoke-WebRequest`, `curl`) get a JS challenge instead of the API. The crawler must:

1. Use **`curl_cffi`** with `impersonate="chrome124"` (or newer) to match Chrome's TLS fingerprint.
2. Send the **browser cookie set** captured from a logged-in Udemy tab. The relevant cookies (in `.udemy.com` / `www.udemy.com` scope) are:
   - `cf_clearance` (Cloudflare challenge pass — short-lived, browser-bound)
   - `__cf_bm` (Cloudflare bot management — short-lived)
   - `access_token`, `dj_session_id`, `ud_user_jwt`, `client_id`, `csrftoken` (Udemy auth/session)
   - `ud_cache_*` and locale cookies (Udemy expects them; missing them flips the cache layer to a different response)
3. Cookies live at `~/Documents/.udemy/cookies.json` (one JSON object: name → value). The crawler reads this once at start.
4. **Token rotation:** `cf_clearance` and `__cf_bm` expire on the order of hours. When the API starts returning HTML challenge pages, the user must re-export cookies from their browser.

There is no Bearer token in this auth scheme — the historic `Authorization: Bearer <token>` header was never set in the captured traffic. Do not send it.

## Listing all quizzes in a course

```
GET https://www.udemy.com/api-2.0/courses/{course_id}/cached-subscriber-curriculum-items/
    ?page_size=100
    &fields[lecture]=title,object_index
    &fields[quiz]=title,object_index,type,num_assessments
```

Response shape:

```json
{
  "count": 5,
  "next": null,
  "previous": null,
  "results": [
    { "_class": "quiz", "id": <quiz-id>, "title": "...", "type": "practice-test", "object_index": 1, "num_assessments": 100 }
  ]
}
```

- Filter `_class == "quiz"`.
- `type` is typically `"practice-test"` for graded quizzes; treat any quiz `_class` as crawl-eligible (don't whitelist `practice-test` only).
- Follow `next` until `null`. Do not compute page numbers.

## Extracting a single quiz

```
GET https://www.udemy.com/api-2.0/quizzes/{quiz_id}/assessments/
    ?version=1
    &draft=false
    &fields[assessment]=@all
    &page_size=250
```

Response shape (one page):

```json
{
  "count": 100,
  "next": null,
  "previous": null,
  "results": [
    {
      "_class": "assessment",
      "id": 124815731,
      "assessment_type": "multiple-choice",
      "section": "Level 1",
      "prompt": {
        "question": "A large financial institution ... Which configuration setting would best meet these requirements?",
        "answers": [
          "Implement a single-level approval workflow with manual revocation.",
          "Use a multi-level approval workflow with auto-revocation rules triggered by HR updates.",
          "..."
        ],
        "feedbacks": ["", "", ""],
        "explanation": "To meet the financial institution's need..."
      },
      "correct_response": ["b"]
    }
  ]
}
```

### Response paths

| Field | Path | Notes |
| --- | --- | --- |
| Question stem | `results[].prompt.question` | HTML-entity-encoded (`&quot;`, `&#x27;`, `&amp;`). Run through `html.unescape()`. |
| Options       | `results[].prompt.answers[]` | List of strings. No option IDs. Position is the identity: index 0 → "a", 1 → "b", … |
| Correct answer | `results[].correct_response` | **List** of single-letter strings, e.g. `["b"]` or `["a","c"]` for multi-answer. Letters match positional indexing of `answers`. |
| Explanation   | `results[].prompt.explanation` | Optional, also HTML-entity-encoded. May be empty string. |
| Type          | `results[].assessment_type` | Observed: `"multiple-choice"` (covers both 6-option MCQs and 2-option True/False). |
| Section       | `results[].section` | Quiz-level grouping label like `"Level 1"`, not per-question. Often the same value across the whole quiz. |
| Quiz title    | (separate endpoint) | See "Quiz metadata" below. |

### Pagination

Although the sample call with `page_size=250` returns all 100 questions in a single response (`next: null`), program defensively: **always follow `next` until `null`**, in case other quizzes exceed 250 items.

### Multi-answer questions

`correct_response` is a list, not a scalar. Render answer keys as a sorted, comma-joined letter string (`"b"` or `"a, c"`). The sample quiz had no multi-answer items, but the field shape supports it and other courses may use it.

## Quiz metadata (for the per-page title)

```
GET https://www.udemy.com/api-2.0/users/me/subscribed-courses/{course_id}/quizzes/{quiz_id}/
    ?draft=false
    &fields[quiz]=id,type,title,description,object_index,num_assessments,version,duration,is_draft,pass_percent,changelog
```

Returns a flat object with `title`, `description` (HTML), `num_assessments`, `pass_percent`. Use `title` for the per-page heading. `description` is HTML and usually a topic list — skip it unless the user asks for it.

The curriculum-items endpoint also returns `title` per quiz, so a separate metadata call per quiz is only needed if you want richer fields (description, pass_percent).

## Course ID derivation

The user's URLs come in three shapes:

| URL shape | How to derive `course_id` |
| --- | --- |
| `udemy.com/course/<slug>/learn/quiz/<quiz_id>` | `<quiz_id>` is in the URL. The `course_id` is **not** in the path; fetch `https://www.udemy.com/api-2.0/courses/?fields[course]=id&page_size=1&search=<slug>` OR follow the HTML page's `<body data-clp-...>` attributes. **Simplest:** ask the user — they almost always know it from their Udemy "My Learning" page (URL `/home/my-courses/learning/?p=<course_id>`). |
| `udemy.com/course/<slug>/learn/lecture/<lecture_id>` | Same as above — `course_id` not in path. |
| `udemy.com/course/<slug>/` | Same. |

**Pragmatic recommendation for `/crawl`:** accept either a course URL **plus** a `--course-id` flag, or detect `course_id` from the `learn/quiz/<quiz_id>` page's embedded JSON. The exploration session here was already given both ids inline, so this codepath was not exhaustively tested.

## Answer source

`correct_response` is present in the GET response. **No POST to `assessment-answers/` is needed**, and `/crawl` must not POST.

## Rate limits observed

None visible in the 4-request sample. No `X-RateLimit-*` headers, no `Retry-After`. The conservative 500ms + 429-backoff rules in `.claude/rules/crawler-conventions.md` remain authoritative; this exploration neither tightens nor relaxes them.

## Worked example (sanitized)

A typical practice-test course in this corpus shape:
- 5 quizzes (`type: "practice-test"`, 100 questions each → 500 total).
- Each quiz titled e.g. "Level N: <topic area>".
- `correct_response` is consistently a list of one letter for the courses tested so far (e.g. `["b"]`), but the field is a list and may carry multi-letter answers for other course shapes.

Sample JSON dumps live in `.claude/skills/explore-udemy/.scratch/` (gitignored).
