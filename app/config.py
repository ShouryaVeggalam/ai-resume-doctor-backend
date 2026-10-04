from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI Resume Doctor API"

    cors_origins: str = (
        "http://localhost:3000,"
        "http://localhost:3001,"
        "http://127.0.0.1:3000,"
        "http://127.0.0.1:3001"
    )

    max_file_size_mb: int = 5

    llm_base_url: str = "https://api.groq.com/openai/v1"

    groq_api_key: str = ""

    llm_model: str = "openai/gpt-oss-120b"

    @property
    def llm_api_key(self) -> str:
        return self.groq_api_key

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()
