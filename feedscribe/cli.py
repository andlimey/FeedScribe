"""FeedScribe CLI entry point."""

import click


@click.group()
def cli():
    """FeedScribe: Monitor YouTube channels and generate AI-powered notes."""
    pass


if __name__ == "__main__":
    cli()
