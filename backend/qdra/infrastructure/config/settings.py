from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_env: str = "development"
    database_url: str
    redis_url: str
    graph_job_queue: str = "graph_reasoning_jobs"
    worker_concurrency: int = 1

    class Config:
        env_file = ".env"


settings = Settings()
