from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL
from pathlib import Path

ENV_DIR = Path(__file__).parent.parent

class Settings(BaseSettings):
    DB_HOST: str
    DB_PORT: int
    DB_USER: str
    DB_PASS: str
    DB_NAME: str

    @property
    def DB_URL_asyncpg(self) -> str:
        return URL.create(
            drivername='postgresql+asyncpg',
            username=self.DB_USER,
            password=self.DB_PASS,
            host=self.DB_HOST,
            port=self.DB_PORT,
            database=self.DB_NAME,
        ).render_as_string(hide_password=False)
    
    model_config = SettingsConfigDict(env_file=ENV_DIR / '.env')

settings = Settings()