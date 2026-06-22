import os
from typing import Optional, BinaryIO
from pathlib import Path

from qdra.infrastructure.storage.image_storage_provider import ImageStorageProvider


class LocalImageStorageProvider:
    """Local filesystem implementation of ImageStorageProvider."""
    
    def __init__(self, storage_root: str):
        self.storage_root = Path(storage_root)
        self.storage_root.mkdir(parents=True, exist_ok=True)
    
    async def save(
        self,
        storage_key: str,
        content: bytes,
        mime_type: str,
    ) -> None:
        """Save image content to local filesystem."""
        file_path = self.storage_root / storage_key
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "wb") as f:
            f.write(content)
    
    async def delete(self, storage_key: str) -> None:
        """Delete image from local filesystem."""
        file_path = self.storage_root / storage_key
        if file_path.exists():
            file_path.unlink()
    
    async def get_public_url(self, storage_key: str) -> Optional[str]:
        """Local storage doesn't have public URLs."""
        return None
    
    async def open_read_stream(self, storage_key: str) -> BinaryIO:
        """Open a read stream for the image."""
        file_path = self.storage_root / storage_key
        if not file_path.exists():
            raise FileNotFoundError(f"Image not found: {storage_key}")
        return open(file_path, "rb")
