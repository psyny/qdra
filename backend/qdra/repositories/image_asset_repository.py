import uuid
from typing import List, Optional

from sqlalchemy.orm import Session

from models.image_asset import ImageAsset
from models.entity import Entity


class ImageAssetRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        entity_id: uuid.UUID,
        storage_backend: str,
        storage_key: str,
        mime_type: str,
        original_filename: Optional[str] = None,
        file_size_bytes: Optional[int] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        alt_text: Optional[str] = None,
        status: str = 'pending',
    ) -> ImageAsset:
        image_asset = ImageAsset(
            entity_id=entity_id,
            storage_backend=storage_backend,
            storage_key=storage_key,
            original_filename=original_filename,
            mime_type=mime_type,
            file_size_bytes=file_size_bytes,
            width=width,
            height=height,
            alt_text=alt_text,
            status=status,
        )
        self.db.add(image_asset)
        self.db.commit()
        self.db.refresh(image_asset)
        return image_asset

    def get_by_id(self, image_asset_id: uuid.UUID) -> Optional[ImageAsset]:
        return self.db.query(ImageAsset).filter(ImageAsset.id == image_asset_id).first()

    def get_primary_image(
        self, entity_id: uuid.UUID
    ) -> Optional[ImageAsset]:
        # Since each entity has only one image, just get the first one
        return (
            self.db.query(ImageAsset)
            .filter(
                ImageAsset.entity_id == entity_id,
                ImageAsset.status == 'ready',
            )
            .first()
        )

    def list_by_entity(
        self, entity_id: uuid.UUID
    ) -> List[ImageAsset]:
        return (
            self.db.query(ImageAsset)
            .filter(
                ImageAsset.entity_id == entity_id,
            )
            .all()
        )

    def delete(self, image_asset_id: uuid.UUID) -> bool:
        image_asset = self.get_by_id(image_asset_id)
        if not image_asset:
            return False
        self.db.delete(image_asset)
        self.db.commit()
        return True

    def update_status(self, image_asset_id: uuid.UUID, status: str) -> ImageAsset:
        """Update the status of an image asset."""
        image_asset = self.get_by_id(image_asset_id)
        if not image_asset:
            raise ValueError("Image asset not found")
        image_asset.status = status
        self.db.commit()
        self.db.refresh(image_asset)
        return image_asset

    def get_by_entity_id(self, entity_id: uuid.UUID) -> List[ImageAsset]:
        """Get all images for an entity."""
        return self.list_by_entity(entity_id)
