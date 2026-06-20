"""Tests for the FeedScribe CLI."""

from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from feedscribe.cli import cli


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def mock_pipeline():
    pipeline = MagicMock()
    pipeline.poll.return_value = []
    pipeline.process_url.return_value = True
    return pipeline


def test_poll_calls_pipeline_poll(runner, mock_pipeline):
    """feedscribe poll calls pipeline.poll()."""
    with patch("feedscribe.cli._build_pipeline", return_value=(mock_pipeline, MagicMock())) as mock_build:
        result = runner.invoke(cli, ["poll"])

    assert result.exit_code == 0
    mock_pipeline.poll.assert_called_once()


def test_process_url_calls_pipeline_process_url(runner, mock_pipeline):
    """feedscribe process <url> calls pipeline.process_url(url, force=False)."""
    url = "https://youtube.com/watch?v=abc123"
    with patch("feedscribe.cli._build_pipeline", return_value=(mock_pipeline, MagicMock())):
        result = runner.invoke(cli, ["process", url])

    assert result.exit_code == 0
    mock_pipeline.process_url.assert_called_once_with(url, force=False)


def test_process_url_with_force_flag(runner, mock_pipeline):
    """feedscribe process <url> --force calls pipeline.process_url(url, force=True)."""
    url = "https://youtube.com/watch?v=abc123"
    with patch("feedscribe.cli._build_pipeline", return_value=(mock_pipeline, MagicMock())):
        result = runner.invoke(cli, ["process", url, "--force"])

    assert result.exit_code == 0
    mock_pipeline.process_url.assert_called_once_with(url, force=True)
