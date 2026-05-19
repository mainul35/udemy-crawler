---
name: generate-word-doc
description: Assemble a Word document from a list of extracted quizzes - one question per page, with a consolidated answer key at the end. Use after the crawler has gathered all quizzes.
---

# Skill: generate-word-doc

## Input

A list of `Quiz` objects:

```python
@dataclass
class Option:
    letter: str   # "A", "B", "C", ...
    text: str
    is_correct: bool

@dataclass
class Question:
    stem: str
    options: list[Option]

@dataclass
class Quiz:
    index: int          # 1-based position in the series
    title: str
    questions: list[Question]
```

Plus a course slug (used for the output filename).

## Output

`output/<course-slug>.docx`

Layout — **one question per page**:

```
Page 1:   Quiz 1 — <title>           (level-2 heading, repeated on every page of this quiz)
          1. <question stem>
             A. option text
             B. option text
             ...
          <page break>
Page 2:   Quiz 1 — <title>
          2. <next question stem>
             ...
          <page break>
...
Page N:   Quiz 2 — <title>            (heading switches when next quiz starts)
          1. <first question of quiz 2>
             ...
...
Final page(s): Answer Key             (level-1 heading)
               Quiz 1 — <title>       (level-2 sub-heading per quiz)
               Q1: B
               Q2: A
               ...
```

The question number resets to 1 at the start of each quiz. The quiz heading repeats on every page so the printed page is self-contained — a reader can identify which quiz a question belongs to without flipping back.

## Implementation rules

Use `python-docx`:

```python
from docx import Document

doc = Document()

for quiz in quizzes:
    for q_num, question in enumerate(quiz.questions, start=1):
        doc.add_heading(f"Quiz {quiz.index} — {quiz.title}", level=2)
        doc.add_paragraph(f"{q_num}. {question.stem}")
        for option in question.options:
            doc.add_paragraph(f"   {option.letter}. {option.text}")
        doc.add_page_break()

doc.add_heading("Answer Key", level=1)
for quiz in quizzes:
    doc.add_heading(f"Quiz {quiz.index} — {quiz.title}", level=2)
    for q_num, question in enumerate(quiz.questions, start=1):
        correct = ", ".join(o.letter for o in question.options if o.is_correct)
        doc.add_paragraph(f"Q{q_num}: {correct}")

doc.save(output_path)
```

The page-break inside the inner loop (after each question) is what produces "one question per page" — do NOT also page-break between quizzes, since the next quiz's first question already starts on a fresh page.

## Edge cases

- **Multi-answer questions** (checkbox): join correct letters with commas.
- **Empty option text** (Udemy sometimes returns `&nbsp;`): strip and skip; warn.
- **Embedded HTML in stem/options**: convert to plain text first using `html2text` or a regex-tag-strip. Preserve nothing — Word docs render the source verbatim.
- **Code snippets**: if the stem contains `<pre>` or `<code>`, render that paragraph in `Courier New` 10pt by setting the run font.

## Filename

Derive `course-slug` from the URL the user originally supplied — the path segment after `/course/`. If that's not available, fall back to the course title slugified (lowercase, spaces → `-`, strip punctuation).
