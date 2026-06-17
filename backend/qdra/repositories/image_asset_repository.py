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
        is_primary: bool = True,
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
            is_primary=is_primary,
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
        return (
            self.db.query(ImageAsset)
            .filter(
                ImageAsset.entity_id == entity_id,
                ImageAsset.is_primary == True,
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

    def set_primary(self, image_asset_id: uuid.UUID) -> Optional[ImageAsset]:
        image_asset = self.get_by_id(image_asset_id)
        if not image_asset:
            return None

        # Unset primary for all images of the same entity
        self.db.query(ImageAsset).filter(
            ImageAsset.entity_id == image_asset.entity_id,
        ).update({"is_primary": False})

        # Set the new primary
        image_asset.is_primary = True
        self.db.commit()
        self.db.refresh(image_asset)
        return image_asset
