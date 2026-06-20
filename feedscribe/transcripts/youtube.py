from youtube_transcript_api import YouTubeTranscriptApi

from feedscribe.models import ContentItem, Transcript
from feedscribe.transcripts.base import Transcriber


class YouTubeTranscriber(Transcriber):
    def fetch(self, item: ContentItem) -> Transcript:
        segments = YouTubeTranscriptApi().fetch(item.id)
        text = " ".join(seg["text"] for seg in segments)
        return Transcript(content_id=item.id, text=text)
