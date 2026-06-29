from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")
    
    app_env: str = "development"
    qdra_service_role: str = "api"
    database_url: str
    redis_url: str = "redis://localhost:6379/0"
    graph_job_queue: str = "graph_reasoning_jobs"
    worker_concurrency: int = 1
    
    # Cache configuration
    l2_caching: bool = True
    cache_entity_ttl: int = 300  # 5 minutes
    cache_relationship_ttl: int = 600  # 10 minutes for material/recipe relationships
    cache_constraint_ttl: int = 600  # 10 minutes for constraint resolution
    cache_permission_ttl: int = 1800  # 30 minutes for user permissions
    
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

    # Deployment configuration
    cors_origins: str = "http://localhost:3000"
    run_migrations_on_startup: bool = False
    log_level: str = "info"

    @model_validator(mode="after")
    def validate_production_settings(self):
        # Validate service role
        allowed_roles = {"api", "worker", "migration"}
        if self.qdra_service_role not in allowed_roles:
            raise ValueError(
                f"QDRA_SERVICE_ROLE must be one of {allowed_roles}, got '{self.qdra_service_role}'"
            )
        
        # Validate production settings based on service role
        if self.app_env == "production":
            if self.qdra_service_role == "api":
                if not self.jwt_secret_key or self.jwt_secret_key == "change-this-in-production":
                    raise ValueError("JWT_SECRET_KEY must be set to a secure value in production for API service")
            # worker and migration roles do not require JWT_SECRET_KEY
        return self


settings = Settings()
