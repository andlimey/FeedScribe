from openai import OpenAI

from feedscribe.models import ContentItem, Notes, Transcript
from feedscribe.utils import to_snake

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


class OpenRouterProvider:
    def __init__(self, api_key: str, models: list[str]) -> None:
        self._client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )
        self._models = models

    def generate_notes(self, item: ContentItem, transcript: Transcript) -> Notes:
        pub_date = item.published_at.date().isoformat()
        prompt = _PROMPT.format(
            title=item.title,
            channel=item.channel,
            url=item.url,
            date=pub_date,
            transcript=transcript.text,
        )
        response = self._client.chat.completions.create(
            model=self._models[0],
            messages=[{"role": "user", "content": prompt}],
            extra_body={"models": self._models},
        )
        markdown = response.choices[0].message.content.strip()
        filename = f"{item.channel}_{to_snake(item.title)}.md"
        return Notes(content_id=item.id, filename=filename, markdown=markdown)
