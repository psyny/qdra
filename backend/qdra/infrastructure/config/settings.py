from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")
    
    app_env: str = "development"
    database_url: str
    redis_url: str = "redis://localhost:6379/0"
    graph_job_queue: str = "graph_reasoning_jobs"
    worker_concurrency: int = 1
    
    # Image storage configuration
    image_storage_backend: str = "local"
    local_storage_root: str = "./uploads"
    max_image_size_mb: int = 5
    allowed_image_mime_types: str = "image/png,image/jpeg,image/webp"
    
    # S3 configuration (for future use)
    s3_bucket: str = ""
    s3_region: str = ""
    s3_endpoint_url: str = ""
    s3_access_key_id: str = ""
    s3_secret_access_key: str = ""
    s3_public_base_url: str = ""


settings = Settings()
