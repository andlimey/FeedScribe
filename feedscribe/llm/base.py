from abc import ABC, abstractmethod

from feedscribe.models import ContentItem, Notes, Transcript


class LLMProvider(ABC):
    @abstractmethod
    def generate_notes(self, item: ContentItem, transcript: Transcript) -> Notes: ...
