from abc import ABC, abstractmethod

from feedscribe.models import ContentItem, Transcript


class Transcriber(ABC):
    @abstractmethod
    def fetch(self, item: ContentItem) -> Transcript: ...
