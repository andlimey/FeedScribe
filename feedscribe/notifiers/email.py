import base64
import re

import resend
from markdown_it import MarkdownIt

from feedscribe.models import ContentItem, Notes


def _channel_display(channel: str) -> str:
    return channel.replace("_", " ").title()


def _strip_frontmatter(content: str) -> str:
    return re.sub(r"^---\n.*?\n---\n+", "", content, count=1, flags=re.DOTALL)


def _build_html_email(notes: Notes) -> str:
    body_md = _strip_frontmatter(notes.markdown)
    md = MarkdownIt(options_update={"linkify": True}).enable("linkify")
    body_html = md.render(body_md)

    return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
           font-size: 16px; line-height: 1.6; color: #1a1a1a;
           background-color: #f5f5f5; margin: 0; padding: 20px; }}
    .container {{ max-width: 680px; margin: 0 auto; background: #fff;
                  border-radius: 8px; padding: 32px 40px; border: 1px solid #e0e0e0; }}
    .subtitle {{ font-size: 13px; color: #888; margin-bottom: 24px;
                 padding-bottom: 16px; border-bottom: 1px solid #e8e8e8; }}
    h2 {{ font-size: 20px; color: #111; border-bottom: 2px solid #e8e8e8;
          padding-bottom: 6px; margin-top: 28px; margin-bottom: 8px; }}
    ul, ol {{ padding-left: 24px; margin: 0 0 12px 0; }}
    li {{ margin-bottom: 4px; }}
    p {{ margin: 0 0 12px 0; }}
    a {{ color: #2563eb; }}
    hr {{ border: none; border-top: 1px solid #e8e8e8; margin: 24px 0; }}
    code {{ background: #f3f4f6; padding: 2px 5px; border-radius: 3px;
            font-size: 14px; font-family: monospace; }}
  </style>
</head>
<body>
  <div class="container">
    <p class="subtitle">{notes.filename}</p>
    {body_html}
  </div>
</body>
</html>"""


class EmailNotifier:
    def __init__(self, api_key: str, from_email: str, to_email: str) -> None:
        resend.api_key = api_key
        self._from_email = from_email
        self._to_email = to_email

    def send(self, item: ContentItem, notes: Notes) -> None:
        channel_display = _channel_display(item.channel)
        subject = f"FeedScribe [{channel_display}]: {item.title}"

        attachment_content = base64.b64encode(notes.markdown.encode("utf-8")).decode("ascii")

        resend.Emails.send(
            {
                "from": self._from_email,
                "to": [self._to_email],
                "subject": subject,
                "html": _build_html_email(notes),
                "attachments": [
                    {
                        "filename": notes.filename,
                        "content": attachment_content,
                    }
                ],
            }
        )
