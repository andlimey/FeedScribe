import pytest
import yaml
from pathlib import Path
from feedscribe.config import load_config, AppConfig, ChannelConfig


def test_load_config(tmp_path):
    cfg_file = tmp_path / "config.yaml"
    cfg_file.write_text(
        """
channels:
  - url: https://www.youtube.com/@test/videos
    name: test_channel
    type: youtube

llm:
  provider: openrouter
  models:
    - google/gemma-4-31b-it:free
    - google/gemini-2.5-flash-lite

notifier:
  provider: email

polling:
  max_videos_per_poll: 3

state:
  path: .feedscribe/processed.json
"""
    )
    config = load_config(str(cfg_file))

    assert isinstance(config, AppConfig)
    assert len(config.channels) == 1
    assert config.channels[0].name == "test_channel"
    assert config.llm.models == ["google/gemma-4-31b-it:free", "google/gemini-2.5-flash-lite"]
    assert config.polling.max_videos_per_poll == 3
    assert config.state.path == ".feedscribe/processed.json"


def test_polling_defaults_to_5(tmp_path):
    cfg_file = tmp_path / "config.yaml"
    cfg_file.write_text(
        """
channels: []
llm:
  provider: openrouter
  models:
    - google/gemma-4-31b-it:free
notifier:
  provider: email
"""
    )
    config = load_config(str(cfg_file))
    assert config.polling.max_videos_per_poll == 5
