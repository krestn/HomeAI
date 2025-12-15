from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    OPENAI_API_KEY: str
    OPENWEBNINJA_API_KEY: str
    GOOGLE_API_KEY: str
    GOOGLE_MAP_API_KEY: str

    class Config:
        env_file = ".env"


settings = Settings()
