import yaml
from pydantic import BaseModel


class ChannelConfig(BaseModel):
    url: str
    name: str


class LLMConfig(BaseModel):
    models: list[str]


class PollingConfig(BaseModel):
    max_videos_per_poll: int = 5


class StateConfig(BaseModel):
    path: str = ".feedscribe/processed.json"


class AppConfig(BaseModel):
    channels: list[ChannelConfig]
    llm: LLMConfig
    polling: PollingConfig = PollingConfig()
    state: StateConfig = StateConfig()


def load_config(path: str = "config.yaml") -> AppConfig:
    with open(path) as f:
        data = yaml.safe_load(f)
    return AppConfig(**data)
