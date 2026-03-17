from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://erp:erp@db:5432/erpdb"
    backend_cors_origins: str = "http://localhost:3000"

    def __init__(self, **data):
        super().__init__(**data)
        # Railway injects DATABASE_URL with the legacy "postgres://" scheme;
        # SQLAlchemy 2.x requires "postgresql://"
        if self.database_url.startswith("postgres://"):
            object.__setattr__(self, "database_url", self.database_url.replace("postgres://", "postgresql://", 1))

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.backend_cors_origins.split(",")]

    class Config:
        env_file = ".env"


settings = Settings()
