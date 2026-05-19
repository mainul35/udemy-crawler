from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Option:
    letter: str
    text: str
    is_correct: bool


@dataclass
class Question:
    stem: str
    options: list[Option]


@dataclass
class Quiz:
    index: int
    title: str
    questions: list[Question] = field(default_factory=list)
