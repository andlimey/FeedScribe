from datetime import datetime
from pydantic import BaseModel


class ContentItem(BaseModel):
    id: str
    title: str
    url: str
    source: str
    channel: str
    published_at: datetime


class Transcript(BaseModel):
    content_id: str
    text: str


class Notes(BaseModel):
    content_id: str
    filename: str
    markdown: str
