from pathlib import Path

import pytest
from pydantic import ValidationError

from skeletal.config import Settings, get_settings


def test_defaults() -> None:
    settings = get_settings()
    assert settings.app_name == "skeletal"
    assert settings.environment == "local"
    assert settings.log_level == "INFO"
    assert settings.log_dir == Path("logs")
    assert settings.log_to_file is True
    assert settings.log_max_bytes == 1_048_576
    assert settings.log_backup_count == 5
    assert settings.api_token is None


def test_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SKELETAL_LOG_LEVEL", "DEBUG")
    settings = get_settings()
    assert settings.log_level == "DEBUG"


def test_dotenv_pickup(tmp_cwd: Path) -> None:
    (tmp_cwd / ".env").write_text("SKELETAL_APP_NAME=from-dotenv\n", encoding="utf-8")
    settings = get_settings()
    assert settings.app_name == "from-dotenv"


def test_invalid_log_level_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SKELETAL_LOG_LEVEL", "NOT_A_LEVEL")
    with pytest.raises(ValidationError):
        get_settings()


def test_redacted_dump_masks_set_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SKELETAL_API_TOKEN", "supersecret")
    dump = get_settings().redacted_dump()
    assert dump["api_token"] == "***"


def test_redacted_dump_none_when_unset() -> None:
    dump = get_settings().redacted_dump()
    assert dump["api_token"] is None


def test_settings_is_frozen() -> None:
    settings = Settings()
    with pytest.raises(ValidationError):
        settings.app_name = "mutated"
