from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Development settings
dot_env_path = Path(__file__).parent / 'dev.env'
# Production settings
# dot_env_path = Path(__file__).parent / '.env'


class EnvSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=dot_env_path,
                                      env_file_encoding='utf-8',
                                      extra='ignore')

    secret: str
    refresh_secret: str
    algorithm: str
    host: str
    port: int
    postgres_host: str
    postgres_user: str
    postgres_password: str
    postgres_db: str
    postgres_port: int
    database_url: str


# production environment
settings = EnvSettings()
