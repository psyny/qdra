from typing import Optional, BinaryIO

from infrastructure.storage.image_storage_provider import ImageStorageProvider


class S3ImageStorageProvider:
    """S3-compatible storage implementation of ImageStorageProvider.
    
    This is a stub for future S3 implementation. The actual S3 integration
    will be added later without changing the API or database model.
    """
    
    def __init__(
        self,
        bucket: str,
        region: str,
        endpoint_url: Optional[str] = None,
        access_key_id: Optional[str] = None,
        secret_access_key: Optional[str] = None,
        public_base_url: Optional[str] = None,
    ):
        self.bucket = bucket
        self.region = region
        self.endpoint_url = endpoint_url
        self.access_key_id = access_key_id
        self.secret_access_key = secret_access_key
        self.public_base_url = public_base_url
    
    async def save(
        self,
        storage_key: str,
        content: bytes,
        mime_type: str,
    ) -> None:
        """Save image content to S3."""
        raise NotImplementedError("S3 storage not yet implemented")
    
    async def delete(self, storage_key: str) -> None:
        """Delete image from S3."""
        raise NotImplementedError("S3 storage not yet implemented")
    
    async def get_public_url(self, storage_key: str) -> Optional[str]:
        """Get public URL for the image if available."""
        if self.public_base_url:
            return f"{self.public_base_url}/{storage_key}"
        return None
    
    async def open_read_stream(self, storage_key: str) -> BinaryIO:
        """Open a read stream for the image."""
        raise NotImplementedError("S3 storage not yet implemented")
