"""Walk a Udemy quiz series and dump the structured quizzes to JSON.

Usage:
    python -m udemy_crawler.cli <udemy-url>

Writes `output/<course-slug>-quizzes.json`. The doc-writer agent picks it up
from there to produce the final .docx.
"""
from __future__ import annotations

import json
import re
import sys
from dataclasses import asdict
from pathlib import Path

from .client import UdemyClient
from .errors import CrawlerError
from .extract import extract_quiz, list_quizzes, resolve_course_id

SLUG_RE = re.compile(r"udemy\.com/course/([^/?#]+)")


def parse_slug(url: str) -> str:
    m = SLUG_RE.search(url)
    if not m:
        raise CrawlerError(f"Could not extract course slug from URL: {url!r}")
    return m.group(1)


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        sys.stderr.write("usage: python -m udemy_crawler.cli <udemy-url>\n")
        return 2

    url = argv[1]
    slug = parse_slug(url)
    client = UdemyClient()

    sys.stderr.write(f"[crawl] resolving course_id for slug={slug!r}\n")
    course_id = resolve_course_id(client, slug)
    sys.stderr.write(f"[crawl] course_id={course_id}\n")

    sys.stderr.write("[crawl] listing quizzes\n")
    quiz_meta = list_quizzes(client, course_id, slug=slug)
    sys.stderr.write(f"[crawl] found {len(quiz_meta)} quizzes\n")

    quizzes = []
    for idx, meta in enumerate(quiz_meta, start=1):
        qid = meta["id"]
        title = meta.get("title") or f"Quiz {idx}"
        sys.stderr.write(f"[crawl] extracting quiz {idx}/{len(quiz_meta)} id={qid} title={title!r}\n")
        quiz = extract_quiz(client, quiz_id=qid, index=idx, title=title, slug=slug)
        sys.stderr.write(f"[crawl]   -> {len(quiz.questions)} questions\n")
        quizzes.append(quiz)

    project_root = Path(__file__).resolve().parents[2]
    out_dir = project_root / "output"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / f"{slug}-quizzes.json"
    payload = {
        "course_slug": slug,
        "course_id": course_id,
        "quizzes": [asdict(q) for q in quizzes],
    }
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    sys.stderr.write(f"[crawl] wrote {out_path}\n")
    print(str(out_path))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv))
    except CrawlerError as e:
        sys.stderr.write(f"ERROR: {e}\n")
        raise SystemExit(1)
