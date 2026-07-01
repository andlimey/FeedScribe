import json
from datetime import datetime, timezone
from pathlib import Path

from feedscribe.models import ContentItem


class JsonStateStore:
    def __init__(self, path: str) -> None:
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        if not self._path.exists():
            self._path.write_text(json.dumps({"processed": []}))

    def _load(self) -> dict:
        return json.loads(self._path.read_text())

    def _save(self, data: dict) -> None:
        self._path.write_text(json.dumps(data, indent=2, default=str))

    def is_processed(self, content_id: str) -> bool:
        data = self._load()
        return any(entry["id"] == content_id for entry in data["processed"])

    def mark_processed(self, item: ContentItem) -> None:
        data = self._load()
        data["processed"].append(
            {
                "id": item.id,
                "url": item.url,
                "title": item.title,
                "channel": item.channel,
                "processed_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        self._save(data)

    def list_processed(self) -> list[dict]:
        return self._load()["processed"]
