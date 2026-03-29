from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    GEMINI_API_KEY: str
    SUPABASE_URL: str
    SUPABASE_KEY: str           # anon key — used for auth token verification
    SUPABASE_SERVICE_KEY: str   # service_role key — used for all DB writes (bypasses RLS)
    GITHUB_TOKEN: Optional[str] = None

    # Database backend: "supabase" (default) or "internal_db" (local PostgreSQL)
    DATABASE: str = "supabase"
    # Required when DATABASE=internal_db
    INTERNAL_DB_URL: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
