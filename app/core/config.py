import logging

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger("goia.config")

DEV_MODEL_ACCESS_CREDENTIALS_SECRET_KEY = "goia-model-access-dev-key"

class Settings(BaseSettings):
  model_config = SettingsConfigDict(env_file=".env", extra="ignore")
  APP_CONTEXT_PATH: str 
  APP_VERSION: str
  
  # Database
  POSTGRES_DB: str
  POSTGRES_HOST: str
  POSTGRES_USER: str
  POSTGRES_PASSWORD: str
  POSTGRES_PORT: int = 5432 

  # Redis
  REDIS_URL: str

  MODEL_ACCESS_CREDENTIALS_SECRET_KEY: str | None = None

  # Rate limits
  RATE_LIMIT_DEFAULT_LIMIT: int = 1000
  RATE_LIMIT_REVEAL_SECRET_LIMIT: int = 10
  RATE_LIMIT_ADMIN_MUTATION_LIMIT: int = 300
  RATE_LIMIT_DEFAULT_WINDOW_SECONDS: int = 3600
  RATE_LIMIT_REVEAL_SECRET_WINDOW_SECONDS: int = 3600
  RATE_LIMIT_ADMIN_MUTATION_WINDOW_SECONDS: int = 3600

  # App
  APP_ENV: str = "development"
  APP_CORS_ORIGINS: str = ""  # comma-separated string — pydantic-settings v2 não aceita list[str] de env
  FIRST_ADMIN_EMAIL: str
  FIRST_ADMIN_PASSWORD: str

  @model_validator(mode="after")
  def validate_secure_production_config(self):
    app_env = self.APP_ENV.lower()

    if not self.MODEL_ACCESS_CREDENTIALS_SECRET_KEY:
      if app_env == "development":
        logger.warning(
          "MODEL_ACCESS_CREDENTIALS_SECRET_KEY ausente; usando chave padrão apenas para desenvolvimento."
        )
        self.MODEL_ACCESS_CREDENTIALS_SECRET_KEY = DEV_MODEL_ACCESS_CREDENTIALS_SECRET_KEY
      else:
        raise ValueError(
          "MODEL_ACCESS_CREDENTIALS_SECRET_KEY deve ser definida fora do ambiente de desenvolvimento"
        )

    if app_env == "production" and not self.APP_CORS_ORIGINS.strip():
      raise ValueError("APP_CORS_ORIGINS deve ser definido em producao")

    return self

  @property
  def cors_origins(self) -> list[str]:
    if not self.APP_CORS_ORIGINS:
      return ["*"]
    return [o.strip() for o in self.APP_CORS_ORIGINS.split(",") if o.strip()]

  @property
  def DATABASE_URL(self) -> str:
    return (
      f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
      f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    )


settings = Settings()
