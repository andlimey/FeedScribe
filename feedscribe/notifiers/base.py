from abc import ABC, abstractmethod

from feedscribe.models import ContentItem, Notes


class Notifier(ABC):
    @abstractmethod
    def send(self, item: ContentItem, notes: Notes) -> None: ...
