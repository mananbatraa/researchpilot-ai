from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    gemini_api_key: str = ""
    tavily_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    # DEMO_MODE=1 replays a canned sample run with no Gemini/Tavily calls (no keys needed).
    demo_mode: bool = False
    # Comma-separated list of origins allowed to call the API, e.g.
    # "https://researchpilot.vercel.app,http://localhost:5173"
    cors_origins: str = "http://localhost:5173"
    # Optional regex for extra origins, e.g. Vercel preview deployments:
    # "https://researchpilot-.*\.vercel\.app"
    cors_origin_regex: str = ""
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip().rstrip("/") for origin in self.cors_origins.split(",") if origin.strip()]

settings = Settings()
