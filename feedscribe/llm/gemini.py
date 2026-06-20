import re
from datetime import date

from google import genai

from feedscribe.llm.base import LLMProvider
from feedscribe.models import ContentItem, Notes, Transcript

_PROMPT = """\
You are a research assistant. Generate structured notes from the following YouTube video transcript.

Video title: {title}
Channel: {channel}
Source URL: {url}
Date: {date}

Transcript:
{transcript}

Output a complete Markdown document with this exact structure:

---
date: {date}
tags:
  - {channel}
  - <2-4 relevant topic tags in snake_case>
source: {url}
---

## TL;DR
<3-5 sentence summary>

## Key Takeaways
- <key point>
- <key point>
- <key point>

## Detailed Notes

### <Topic 1>
<notes>

### <Topic 2>
<notes>

Output only the Markdown document, nothing else.\
"""


def _title_to_snake(title: str) -> str:
    title = re.sub(r"[^\w\s]", "", title.lower())
    return re.sub(r"\s+", "_", title.strip())


class GeminiProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "gemini-2.5-flash") -> None:
        self._client = genai.Client(api_key=api_key)
        self._model = model

    def generate_notes(self, item: ContentItem, transcript: Transcript) -> Notes:
        today = date.today().isoformat()
        prompt = _PROMPT.format(
            title=item.title,
            channel=item.channel,
            url=item.url,
            date=today,
            transcript=transcript.text,
        )
        response = self._client.models.generate_content(
            model=self._model,
            contents=prompt,
        )
        markdown = response.text.strip()
        filename = f"{item.channel}_{_title_to_snake(item.title)}.md"
        return Notes(content_id=item.id, filename=filename, markdown=markdown)
