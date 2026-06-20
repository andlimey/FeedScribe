"""FeedScribe CLI entry point."""

import os

import click
from dotenv import load_dotenv

from feedscribe.config import AppConfig, load_config
from feedscribe.llm.gemini import GeminiProvider
from feedscribe.notifiers.email import EmailNotifier
from feedscribe.pipeline import Pipeline
from feedscribe.sources.youtube import YouTubeSource
from feedscribe.state import JsonStateStore
from feedscribe.transcripts.youtube import YouTubeTranscriber


def _build_pipeline(config_path: str = "config.yaml") -> tuple[Pipeline, AppConfig]:
    load_dotenv()
    config = load_config(config_path)
    state = JsonStateStore(config.state.path)
    source = YouTubeSource()
    transcriber = YouTubeTranscriber()
    llm = GeminiProvider(
        api_key=os.environ["GEMINI_API_KEY"],
        model=config.llm.model,
    )
    notifier = EmailNotifier(
        api_key=os.environ["RESEND_API_KEY"],
        from_email=os.environ["RESEND_FROM_EMAIL"],
        to_email=os.environ["RESEND_TO_EMAIL"],
    )
    return Pipeline(source, transcriber, llm, notifier, state), config


@click.group()
def cli() -> None:
    """FeedScribe: Monitor YouTube channels and generate AI-powered notes."""
    pass


@cli.command()
@click.option("--config", "config_path", default="config.yaml", show_default=True)
def poll(config_path: str) -> None:
    """Check all configured channels and process new videos."""
    pipeline, config = _build_pipeline(config_path)
    processed = pipeline.poll(config)
    if processed:
        click.echo(f"Processed {len(processed)} video(s): {', '.join(processed)}")
    else:
        click.echo("No new videos found.")


@cli.command()
@click.argument("url")
@click.option("--force", is_flag=True, default=False, help="Reprocess even if already seen.")
@click.option("--config", "config_path", default="config.yaml", show_default=True)
def process(url: str, force: bool, config_path: str) -> None:
    """Process a specific YouTube video by URL or ID."""
    pipeline, _ = _build_pipeline(config_path)
    success = pipeline.process_url(url, force=force)
    if success:
        click.echo(f"Processed: {url}")
    else:
        click.echo("Already processed. Use --force to reprocess.")


if __name__ == "__main__":
    cli()
