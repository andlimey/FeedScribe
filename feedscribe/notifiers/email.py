import markdown as md
import resend

from feedscribe.models import ContentItem, Notes
from feedscribe.notifiers.base import Notifier


def _channel_display(channel: str) -> str:
    return channel.replace("_", " ").title()


class EmailNotifier(Notifier):
    def __init__(self, api_key: str, from_email: str, to_email: str) -> None:
        resend.api_key = api_key
        self._from_email = from_email
        self._to_email = to_email

    def send(self, item: ContentItem, notes: Notes) -> None:
        channel_display = _channel_display(item.channel)
        subject = f"FeedScribe [{channel_display}]: {item.title}"

        html_body = md.markdown(notes.markdown, extensions=["fenced_code", "tables"])

        resend.Emails.send(
            {
                "from": self._from_email,
                "to": self._to_email,
                "subject": subject,
                "html": html_body,
                "attachments": [
                    {
                        "filename": notes.filename,
                        "content": list(notes.markdown.encode("utf-8")),
                    }
                ],
            }
        )
