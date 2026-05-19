---
description: Probe a Udemy quiz series to codify navigation and extraction into the extract-quiz skill
argument-hint: <quiz-series-url>
---

The user wants to discover Udemy's quiz API structure for: **$ARGUMENTS**

This command exists because the crawler's navigation/extraction logic is **not pre-known**. Your job is to find out, then write the findings into `.claude/skills/extract-quiz/SKILL.md` so future `/crawl` runs can rely on it.

Steps:

1. **Confirm prerequisites.**
   - Verify `~/Documents/.udemy/` exists and contains a readable token file. If not, stop and tell the user to create it.
   - Verify the URL looks like a Udemy course/quiz URL.

2. **Spawn the `page-explorer` agent** (see `.claude/agents/page-explorer.md`). Give it the URL and the token location. Instruct it to:
   - Identify whether the URL points to a course landing page, a curriculum item, or a quiz directly.
   - Probe the likely Udemy REST endpoints (e.g. `/api-2.0/courses/{id}/cached-subscriber-curriculum-items/`, `/api-2.0/quizzes/{id}/assessments/`) and record the actual URLs that work, query params, and response JSON shape.
   - Test pagination — find a series with >10 quizzes and verify the `next`/`previous` link semantics.
   - Locate where correct answers live in the JSON (often a `correct_response` field; sometimes only revealed after a submission POST).
   - Note any rate-limit headers observed.

3. **Codify the findings.** Have the agent rewrite `.claude/skills/extract-quiz/SKILL.md`, replacing the stub body with a concrete description:
   - The exact endpoint URL pattern(s) to call.
   - The JSON path to question text, options, and correct answer.
   - Pagination rules.
   - Any auth header requirements beyond the bearer token.

4. **Verify.** Read the rewritten skill file back. Confirm there is no remaining `STUB —` marker. Print a short summary of what was learned (endpoints, fields, pagination strategy).

After this command succeeds, `/crawl $ARGUMENTS` should work end-to-end.
