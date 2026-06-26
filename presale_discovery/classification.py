from __future__ import annotations

from datetime import date, datetime

from models import ProjectResult

STATUSES = {"past", "live", "upcoming", "unknown"}


def classify_project(project: ProjectResult) -> str:
    explicit = (project.status or "").lower().strip()
    if explicit in STATUSES and explicit != "unknown":
        return explicit

    today = date.today()
    start = _parse_date(project.start_date)
    end = _parse_date(project.end_date)

    if start and start > today:
        return "upcoming"
    if start and start <= today and (end is None or end >= today):
        return "live"
    if end and end < today:
        return "past"

    context = " ".join(
        [
            project.project_name,
            project.summary,
            project.source_url,
            project.website,
        ]
    ).lower()

    if any(keyword in context for keyword in ["sold out", "ended", "closed", "finished"]):
        return "past"
    if any(keyword in context for keyword in ["live", "ongoing", "now open", "buy now"]):
        return "live"
    if any(keyword in context for keyword in ["upcoming", "coming soon", "launching", "opens on"]):
        return "upcoming"

    return "unknown"


def _parse_date(value: str | None):
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None
