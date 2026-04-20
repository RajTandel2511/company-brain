from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    spectrum_sql_host: str
    spectrum_sql_port: int = 1433
    spectrum_sql_database: str = "Spectrum"
    spectrum_sql_user: str
    spectrum_sql_password: str
    spectrum_sql_encrypt: str = "yes"
    spectrum_sql_trust_cert: str = "yes"
    spectrum_company_code: str = "AA1"

    # LLM
    llm_provider: str = "anthropic"  # "anthropic" | "ollama"
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-haiku-4-5-20251001"
    anthropic_summary_model: str = ""
    ollama_base_url: str = "http://host.docker.internal:11434"
    ollama_model: str = "qwen2.5-coder:7b"

    response_cache_ttl: int = 3600

    nas_root: str = "/mnt/nas"
    app_secret: str = "change-me"
    allowed_origins: str = "*"


settings = Settings()
