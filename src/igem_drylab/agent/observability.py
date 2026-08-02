from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


class EventLogger:
    """Structured run event logger.

    TODO: persist JSONL traces, attach tool stdout/stderr summaries, and export
    run metadata to the future wiki visualization layer.
    """

    def __init__(self) -> None:
        self.events: list[dict[str, Any]] = []

    def emit(self, event_type: str, **payload: Any) -> None:
        self.events.append(
            {
                "event_type": event_type,
                "created_at": datetime.now(timezone.utc).isoformat(),
                **payload,
            }
        )
