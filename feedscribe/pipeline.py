from feedscribe.config import AppConfig
from feedscribe.llm.gemini import GeminiProvider
from feedscribe.models import ContentItem
from feedscribe.notifiers.email import EmailNotifier
from feedscribe.sources.youtube import YouTubeSource
from feedscribe.state import JsonStateStore
from feedscribe.transcripts.youtube import YouTubeTranscriber


class Pipeline:
    def __init__(
        self,
        source: YouTubeSource,
        transcriber: YouTubeTranscriber,
        llm: GeminiProvider,
        notifier: EmailNotifier,
        state: JsonStateStore,
    ) -> None:
        self._source = source
        self._transcriber = transcriber
        self._llm = llm
        self._notifier = notifier
        self._state = state

    def process_item(self, item: ContentItem) -> None:
        transcript = self._transcriber.fetch(item)
        notes = self._llm.generate_notes(item, transcript)
        self._notifier.send(item, notes)
        self._state.mark_processed(item)

    def poll(self, config: AppConfig) -> list[str]:
        processed = []
        for channel_cfg in config.channels:
            items = self._source.fetch_recent(channel_cfg, config.polling.max_videos_per_poll)
            for item in items:
                if not self._state.is_processed(item.id):
                    self.process_item(item)
                    processed.append(item.id)
        return processed

    def process_url(self, url_or_id: str, force: bool = False) -> bool:
        item = self._source.fetch_by_url(url_or_id)
        if not force and self._state.is_processed(item.id):
            return False
        self.process_item(item)
        return True
