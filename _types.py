from dataclasses import dataclass, field, asdict
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
    # Note: These need to reflect in the Notion DB and
    # notion_utils functions.

    page_id: str | None = None
    title: str | None = None
    url: str | None = None
    arxiv_id: str | None = None
    focus: Focus | None = None
    summary: str | None = None
    abstract: str | None = None
    authors: list[str] = field(default_factory=list)
    published: datetime | None = None
    explored: bool | None = None

    # We don't want to excessively write back to Notion, so we'll
    # offer the ability to set change tracking when we read.

    track_changes: bool = False

    def __post_init__(self):
        self._original_state = asdict(self)

    def has_changed(self):
        if self.track_changes:
            return self._original_state != asdict(self)
        else:
            return True
    
    def has_arxiv_props(self) -> bool:
        return all(
            [
                self.title,
                self.url,
                self.authors,
                self.published,
            ]
        )