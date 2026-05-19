---
description: Crawl a Udemy quiz series and emit a Word document
argument-hint: <quiz-series-url>
---

The user wants to crawl the Udemy quiz series at: **$ARGUMENTS**

Follow these steps **in order**:

1. **Guard against an unconfigured skill.** Read `.claude/skills/extract-quiz/SKILL.md`. If the body still contains the literal string `STUB —` (the un-populated marker), stop and tell the user:
   > `extract-quiz/SKILL.md` has not been codified yet. Run `/explore-udemy $ARGUMENTS` first so the skill knows how to navigate this course.

   Do NOT attempt to guess endpoints — that's what the explore step is for.

2. **Load the token.** Read it from `~/Documents/.udemy/` using the helper described in `CLAUDE.md > Authentication`. If the directory is missing, fail with a clear message that points the user to create it. Never print the token.

3. **Walk the series.** Use the endpoints and JSON paths recorded in `extract-quiz/SKILL.md`. Honour the pagination rule ("follow `next` until null") from `.claude/rules/crawler-conventions.md`. Respect the 500 ms inter-request floor and exponential backoff on HTTP 429.

4. **Assemble the document.** Hand the collected quiz list to the `doc-writer` agent — it follows `.claude/skills/generate-word-doc/SKILL.md` to produce `output/<course-slug>.docx` with one quiz per page and the answer key on the final page.

5. **Report.** Print the output path and the count of quizzes written.

If anything in steps 2–4 fails, surface the error verbatim and stop. Do not silently skip quizzes.
