from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables or a .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Ecommerce SaaS API"
    version: str = "0.1.0"
    environment: str = "development"
    cors_origins: list[str] = ["http://localhost:5173"]

    # PostgreSQL connection string. Override with DATABASE_URL in the environment
    # or in backend/.env. The +asyncpg suffix selects the async driver.
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/ecommerce_saas"

    # Supabase requires TLS. Disable only for a local PostgreSQL without SSL.
    db_ssl: bool = True

    # The Supabase transaction pooler (port 6543) does not support prepared
    # statements. Set this to true when using transaction mode.
    db_disable_prepared_statements: bool = False

    # Keep the application pool small when connecting through Supabase's pooler.
    db_pool_size: int = 5
    db_max_overflow: int = 5

    sql_echo: bool = False

    # JWT signing settings. JWT_SECRET_KEY is required and must be set in .env.
    jwt_secret_key: SecretStr
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30


# model_validate({}) loads values from environment/.env while keeping the
# required SecretStr field explicit for type checkers.
settings = Settings.model_validate({})
