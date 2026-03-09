from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://erp:erp@db:5432/erpdb"
    backend_cors_origins: str = "http://localhost:3000"

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.backend_cors_origins.split(",")]

    class Config:
        env_file = ".env"


settings = Settings()
