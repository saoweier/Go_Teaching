from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BACKEND_DIR.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Go Teaching Backend"
    app_env: str = "development"
    katago_executable: Path = Field(default=PROJECT_ROOT / "tools/katago/opencl/katago.exe")
    katago_model: Path = Field(
        default=PROJECT_ROOT / "models/katago/kata1-b18c384nbt-s9372115968-d4150170048.bin.gz"
    )
    katago_analysis_config: Path = Field(default=PROJECT_ROOT / "config/katago-analysis.cfg")
    default_board_size: int = 19
    default_komi: float = 7.5
    default_rules: str = "tromp-taylor"
    cors_origins: str = "http://127.0.0.1:5173,http://localhost:5173"
    cors_origin_regex: str = r"^https?://((localhost|127\.0\.0\.1)|((10|192\.168|172\.(1[6-9]|2\d|3[0-1]))\.\d+\.\d+))(:\d+)?$"

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]


def _resolve_project_path(path: Path) -> Path:
    if path.is_absolute():
        return path
    return (BACKEND_DIR / path).resolve()


settings = Settings()
settings.katago_executable = _resolve_project_path(settings.katago_executable)
settings.katago_model = _resolve_project_path(settings.katago_model)
settings.katago_analysis_config = _resolve_project_path(settings.katago_analysis_config)
