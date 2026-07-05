from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Roadcast API"
    cors_origins: list[str] = ["http://localhost:3000"]

    # LLM (через тот же прокси-провайдер, что и в optics_summary)
    llm_provider: str = "polza"
    polza_ai_api_key: str = ""
    polza_ai_base_url: str = "https://polza.ai/api/v1"
    claude_model: str = "anthropic/claude-sonnet-4.5"

    # Routing / geo
    routing_provider: str = "osrm"
    yandex_maps_api_key: str = ""

    # TTS
    tts_provider: str = "openai"
    tts_api_key: str = ""

    # Database
    database_url: str = "postgresql+asyncpg://user:password@localhost:5432/roadcast"


settings = Settings()
