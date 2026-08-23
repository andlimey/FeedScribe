import re


def to_snake(text: str) -> str:
    text = re.sub(r"[^\w\s]", "", text.lower())
    return re.sub(r"\s+", "_", text.strip())


def channel_display(channel: str) -> str:
    return channel.replace("_", " ").title()


_FORBIDDEN_FILENAME_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def sanitize_filename(text: str) -> str:
    return _FORBIDDEN_FILENAME_CHARS.sub("", text).strip().rstrip(".")
