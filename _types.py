from dataclasses import dataclass
from datetime import datetime
from enum import Enum

class Focus(str, Enum):
    Offensive = "Offensive"
    Defensive = "Defensive"
    Adversarial = "Adversarial"
    Safety = "Safety"
    Other = "Other"

@dataclass
class Paper:
    page_id: str | None
    title: str | None
    url: str | None
    arxiv_id: str | None
    focus: Focus | None
    summary: str | None
    abstract: str | None
    authors: list[str]
    published: datetime | None
