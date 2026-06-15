from typing import Protocol, Optional, BinaryIO
from abc import ABC, abstractmethod


class ImageStorageProvider(Protocol):
    """Protocol for image storage backends (local, S3, etc.)."""
    
    async def save(
        self,
        storage_key: str,
        content: bytes,
        mime_type: str,
    ) -> None:
        """Save image content to storage."""
        ...
    
    async def delete(self, storage_key: str) -> None:
        """Delete image from storage."""
        ...
    
    async def get_public_url(self, storage_key: str) -> Optional[str]:
        """Get public URL for the image if available."""
        ...
    
    async def open_read_stream(self, storage_key: str) -> BinaryIO:
        """Open a read stream for the image."""
        ...
