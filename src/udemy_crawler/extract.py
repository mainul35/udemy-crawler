from __future__ import annotations

from .client import UdemyClient
from .errors import CourseIdUnresolved
from .models import Option, Question, Quiz
from .text import clean_html

BASE = "https://www.udemy.com/api-2.0"
MAX_QUIZZES = 500
LETTERS = "abcdefghijklmnopqrstuvwxyz"


def resolve_course_id(client: UdemyClient, slug: str) -> int:
    """Look up a course's numeric id by its URL slug."""
    url = f"{BASE}/courses/{slug}/?fields[course]=id"
    data = client.get_json(url, referer=f"https://www.udemy.com/course/{slug}/")
    cid = data.get("id")
    if not isinstance(cid, int):
        raise CourseIdUnresolved(f"slug={slug!r} did not resolve to a numeric id (got {cid!r})")
    return cid


def list_quizzes(client: UdemyClient, course_id: int, *, slug: str) -> list[dict]:
    """Return raw curriculum entries with `_class == 'quiz'`, in series order."""
    referer = f"https://www.udemy.com/course/{slug}/learn/"
    url = (
        f"{BASE}/courses/{course_id}/cached-subscriber-curriculum-items/"
        "?page_size=100&fields[lecture]=title,object_index"
        "&fields[quiz]=title,object_index,type,num_assessments"
    )
    quizzes: list[dict] = []
    while url:
        data = client.get_json(url, referer=referer)
        quizzes.extend(r for r in data.get("results", []) if r.get("_class") == "quiz")
        if len(quizzes) >= MAX_QUIZZES:
            quizzes = quizzes[:MAX_QUIZZES]
            break
        url = data.get("next")
    quizzes.sort(key=lambda q: q.get("object_index", 0))
    return quizzes


def extract_quiz(client: UdemyClient, *, quiz_id: int, index: int, title: str, slug: str) -> Quiz:
    """Walk the assessments endpoint for a single quiz; return a populated Quiz."""
    referer = f"https://www.udemy.com/course/{slug}/learn/quiz/{quiz_id}/test"
    url = (
        f"{BASE}/quizzes/{quiz_id}/assessments/"
        "?version=1&draft=false&fields[assessment]=@all&page_size=250"
    )
    quiz = Quiz(index=index, title=clean_html(title))
    while url:
        data = client.get_json(url, referer=referer)
        for a in data.get("results", []):
            q = _to_question(a)
            if q is not None:
                quiz.questions.append(q)
        url = data.get("next")
    return quiz


def _to_question(assessment: dict) -> Question | None:
    prompt = assessment.get("prompt") or {}
    raw_answers = prompt.get("answers") or []
    if not raw_answers:
        return None
    correct = {c.lower() for c in (assessment.get("correct_response") or []) if isinstance(c, str)}
    options: list[Option] = []
    for i, raw_text in enumerate(raw_answers):
        if i >= len(LETTERS):
            break
        cleaned = clean_html(raw_text)
        if not cleaned:
            continue
        options.append(
            Option(
                letter=LETTERS[i].upper(),
                text=cleaned,
                is_correct=LETTERS[i] in correct,
            )
        )
    if not options:
        return None
    stem = clean_html(prompt.get("question"))
    return Question(stem=stem, options=options)
