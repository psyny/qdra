import uuid
import imghdr
from typing import Optional, Tuple
from PIL import Image
import io

from sqlalchemy.orm import Session

from repositories.image_asset_repository import ImageAssetRepository
from repositories.entity_repository import EntityRepository
from infrastructure.storage.local_image_storage_provider import LocalImageStorageProvider
from infrastructure.storage.s3_image_storage_provider import S3ImageStorageProvider
from infrastructure.storage.image_storage_provider import ImageStorageProvider
from infrastructure.config.settings import settings


class ImageService:
    def __init__(self, db: Session):
        self.db = db
        self.image_asset_repo = ImageAssetRepository(db)
        self.entity_repo = EntityRepository(db)
        self.storage_provider = self._get_storage_provider()
    
    def _get_storage_provider(self) -> ImageStorageProvider:
        """Get the configured storage provider."""
        if settings.image_storage_backend == "local":
            return LocalImageStorageProvider(settings.local_storage_root)
        elif settings.image_storage_backend == "s3":
            return S3ImageStorageProvider(
                bucket=settings.s3_bucket,
                region=settings.s3_region,
                endpoint_url=settings.s3_endpoint_url or None,
                access_key_id=settings.s3_access_key_id or None,
                secret_access_key=settings.s3_secret_access_key or None,
                public_base_url=settings.s3_public_base_url or None,
                force_path_style=getattr(settings, 's3_force_path_style', False),
            )
        else:
            raise ValueError(f"Unknown storage backend: {settings.image_storage_backend}")
    
    def _validate_image(self, content: bytes, filename: str) -> Tuple[str, str]:
        """Validate image type and size. Returns (mime_type, extension)."""
        # Check file size
        max_size = settings.max_image_size_mb * 1024 * 1024
        if len(content) > max_size:
            raise ValueError(f"Image size exceeds {settings.max_image_size_mb}MB limit")
        
        # Detect actual image type from content
        image_type = imghdr.what(None, h=content)
        if image_type not in ["png", "jpeg", "webp"]:
            raise ValueError(f"Unsupported image type: {image_type}")
        
        # Map to MIME type
        mime_type_map = {
            "png": "image/png",
            "jpeg": "image/jpeg",
            "webp": "image/webp",
        }
        mime_type = mime_type_map[image_type]
        
        # Check if MIME type is allowed
        allowed_types = [t.strip() for t in settings.allowed_image_mime_types.split(",")]
        if mime_type not in allowed_types:
            raise ValueError(f"MIME type {mime_type} not allowed")
        
        return mime_type, f".{image_type}"
    
    def _get_image_dimensions(self, content: bytes) -> Tuple[int, int]:
        """Extract image dimensions."""
        image = Image.open(io.BytesIO(content))
        return image.size
    
    def _generate_storage_key(
        self, project_id: uuid.UUID, entity_id: uuid.UUID, image_asset_id: uuid.UUID, extension: str
    ) -> str:
        """Generate storage key for an image."""
        return f"projects/{project_id}/entities/{entity_id}/images/{image_asset_id}{extension}"
    
    async def upload_entity_image(
        self,
        project_id: uuid.UUID,
        entity_id: uuid.UUID,
        content: bytes,
        filename: str,
        alt_text: Optional[str] = None,
    ):
        """Upload an image for an entity."""
        entity = self.entity_repo.get_by_id(entity_id)
        if not entity or entity.project_id != project_id:
            raise ValueError("Entity not found")

        mime_type, extension = self._validate_image(content, filename)
        width, height = self._get_image_dimensions(content)

        image_asset_id = uuid.uuid4()
        storage_key = self._generate_storage_key(project_id, entity_id, image_asset_id, extension)

        await self.storage_provider.save(storage_key, content, mime_type)

        image_asset = self.image_asset_repo.create(
            entity_id=entity_id,
            storage_backend=settings.image_storage_backend,
            storage_key=storage_key,
            mime_type=mime_type,
            original_filename=filename,
            file_size_bytes=len(content),
            width=width,
            height=height,
            alt_text=alt_text,
            is_primary=True,
        )

        return image_asset

    def get_entity_image(self, entity_id: uuid.UUID):
        """Get the primary image for an entity."""
        return self.image_asset_repo.get_primary_image(entity_id)
    
    def get_image_by_id(self, image_asset_id: uuid.UUID):
        """Get an image by its ID."""
        return self.image_asset_repo.get_by_id(image_asset_id)
    
    async def delete_image(self, image_asset_id: uuid.UUID):
        """Delete an image."""
        image_asset = self.image_asset_repo.get_by_id(image_asset_id)
        if not image_asset:
            raise ValueError("Image not found")
        
        # Delete from storage
        await self.storage_provider.delete(image_asset.storage_key)
        
        # Delete from database
        self.image_asset_repo.delete(image_asset_id)
    
    async def get_image_stream(self, image_asset_id: uuid.UUID):
        """Get a read stream for an image."""
        image_asset = self.image_asset_repo.get_by_id(image_asset_id)
        if not image_asset:
            raise ValueError("Image not found")
        
        return await self.storage_provider.open_read_stream(image_asset.storage_key)
    
    async def presign_upload(
        self,
        entity_id: uuid.UUID,
        filename: str,
        mime_type: str,
        file_size_bytes: int,
        width: int,
        height: int,
        alt_text: Optional[str] = None,
    ):
        """Create a presigned upload URL for an image."""
        entity = self.entity_repo.get_by_id(entity_id)
        if not entity:
            raise ValueError("Entity not found")
        
        # Validate dimensions match project image size
        project = entity.project
        if width != project.image_size_px or height != project.image_size_px:
            raise ValueError(f"Image dimensions must be {project.image_size_px}x{project.image_size_px}")
        
        # Validate square image
        if width != height:
            raise ValueError("Image must be square")
        
        # Validate MIME type
        allowed_types = [t.strip() for t in settings.allowed_image_mime_types.split(",")]
        if mime_type not in allowed_types:
            raise ValueError(f"MIME type {mime_type} not allowed")
        
        # Validate file size
        max_size = settings.max_image_size_mb * 1024 * 1024
        if file_size_bytes > max_size:
            raise ValueError(f"Image size exceeds {settings.max_image_size_mb}MB limit")
        
        # Delete any existing image for this entity (one image per entity)
        existing_images = self.image_asset_repo.get_by_entity_id(entity_id)
        for existing_image in existing_images:
            try:
                await self.storage_provider.delete(existing_image.storage_key)
            except Exception:
                pass
            self.image_asset_repo.delete(existing_image.id)
        
        # Create image asset record in pending state
        image_asset_id = uuid.uuid4()
        extension = self._get_extension_from_mime_type(mime_type)
        storage_key = self._generate_storage_key(entity.project_id, entity_id, image_asset_id, extension)
        
        image_asset = self.image_asset_repo.create(
            entity_id=entity_id,
            storage_backend=settings.image_storage_backend,
            storage_key=storage_key,
            mime_type=mime_type,
            original_filename=filename,
            file_size_bytes=file_size_bytes,
            width=width,
            height=height,
            alt_text=alt_text,
            status='pending',
        )
        
        # Generate presigned upload URL
        upload_url = await self.storage_provider.create_presigned_upload_url(
            storage_key=storage_key,
            content_type=mime_type,
            expires_in_seconds=3600,
        )
        
        return {
            "image_asset_id": image_asset.id,
            "upload_url": upload_url,
            "storage_key": storage_key,
        }
    
    async def finalize_upload(self, image_asset_id: uuid.UUID):
        """Finalize an image upload after the file is uploaded to storage."""
        image_asset = self.image_asset_repo.get_by_id(image_asset_id)
        if not image_asset:
            raise ValueError("Image asset not found")
        
        # Check if object exists in storage
        exists = await self.storage_provider.object_exists(image_asset.storage_key)
        if not exists:
            # Delete the pending record
            self.image_asset_repo.delete(image_asset_id)
            raise ValueError("Uploaded object not found in storage")
        
        # Mark as ready
        image_asset = self.image_asset_repo.update_status(image_asset_id, 'ready')
        
        # Generate public URL
        public_url = await self.storage_provider.get_public_url(image_asset.storage_key)
        
        return {
            "id": image_asset.id,
            "entity_id": image_asset.entity_id,
            "mime_type": image_asset.mime_type,
            "width": image_asset.width,
            "height": image_asset.height,
            "url": public_url,
        }
    
    def get_entity_images(self, entity_id: uuid.UUID):
        """Get all images for an entity."""
        return self.image_asset_repo.get_by_entity_id(entity_id)
    
    def _get_extension_from_mime_type(self, mime_type: str) -> str:
        """Get file extension from MIME type."""
        mime_to_ext = {
            "image/png": ".png",
            "image/jpeg": ".jpg",
            "image/webp": ".webp",
        }
        return mime_to_ext.get(mime_type, ".jpg")
