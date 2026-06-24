from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")
    
    app_env: str = "development"
    database_url: str
    redis_url: str = "redis://localhost:6379/0"
    graph_job_queue: str = "graph_reasoning_jobs"
    worker_concurrency: int = 1
    
    # Cache configuration
    cache_entity_local_size: int = 1000
    cache_entity_local_ttl: int = 300  # 5 minutes
    cache_entity_redis_ttl: int = 3600  # 1 hour
    cache_relationship_ttl: int = 600  # 10 minutes for material/recipe relationships
    cache_permission_ttl: int = 1800  # 30 minutes for user permissions
    l1_caching: bool = True
    l2_caching: bool = True
    
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
    s3_force_path_style: bool = False
    
    # JWT configuration
    jwt_secret_key: str = "change-this-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24


settings = Settings()
