import types
from functools import lru_cache
from pathlib import Path
from typing import Literal, get_args, get_origin

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


def _is_secret_annotation(annotation: object) -> bool:
    if annotation is SecretStr:
        return True
    if get_origin(annotation) is types.UnionType:
        return SecretStr in get_args(annotation)
    return False


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="SKELETAL_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        frozen=True,
    )

    app_name: str = "skeletal"
    environment: Literal["local", "dev", "staging", "prod"] = "local"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    log_dir: Path = Path("logs")
    log_to_file: bool = True
    log_max_bytes: int = Field(default=1_048_576, ge=1024)
    log_backup_count: int = Field(default=5, ge=0)
    api_token: SecretStr | None = None

    def redacted_dump(self) -> dict[str, object]:
        dump = self.model_dump(mode="json")
        for name, field in type(self).model_fields.items():
            if _is_secret_annotation(field.annotation):
                value = getattr(self, name)
                dump[name] = "***" if value is not None else None
        return dump


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
