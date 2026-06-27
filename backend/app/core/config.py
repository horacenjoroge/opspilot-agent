from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = Field(default="opspilot", alias="APP_NAME")
    app_env: str = Field(default="development", alias="APP_ENV")
    app_host: str = Field(default="0.0.0.0", alias="APP_HOST")
    app_port: int = Field(default=8000, alias="APP_PORT")
    app_reload: bool = Field(default=False, alias="APP_RELOAD")
    enable_auth: bool = Field(default=False, alias="ENABLE_AUTH")
    enable_dashboard_auth: bool = Field(default=False, alias="ENABLE_DASHBOARD_AUTH")
    enable_demo_routes: bool = Field(default=True, alias="ENABLE_DEMO_ROUTES")
    enable_eval_routes: bool = Field(default=True, alias="ENABLE_EVAL_ROUTES")
    enable_dashboard: bool = Field(default=True, alias="ENABLE_DASHBOARD")
    enable_metrics: bool = Field(default=True, alias="ENABLE_METRICS")
    auth_session_cookie_name: str = Field(default="opspilot_session", alias="AUTH_SESSION_COOKIE_NAME")
    auth_session_ttl_hours: int = Field(default=24, alias="AUTH_SESSION_TTL_HOURS")
    require_approval_for_medium_risk: bool = Field(default=True, alias="REQUIRE_APPROVAL_FOR_MEDIUM_RISK")
    database_url: str = Field(default="sqlite:///./opspilot.db", alias="DATABASE_URL")
    llm_provider: str = Field(default="qwen", alias="LLM_PROVIDER")
    qwen_api_key: str = Field(default="", alias="QWEN_API_KEY")
    qwen_model: str = Field(default="qwen3.7-plus", alias="QWEN_MODEL")
    qwen_base_url: str = Field(
        default="https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
        alias="QWEN_BASE_URL",
    )
    qwen_reasoning_model: str = Field(
        default="qwen3.7-max",
        alias="QWEN_REASONING_MODEL",
    )
    webhook_secret: str = Field(default="", alias="WEBHOOK_SECRET")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        populate_by_name=True,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
