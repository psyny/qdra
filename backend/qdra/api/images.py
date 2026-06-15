import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from db.session import get_db
from services.image_service import ImageService

router = APIRouter()


class ImageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    project_id: uuid.UUID
    owner_type: str
    owner_id: uuid.UUID
    storage_backend: str
    storage_key: str
    mime_type: str
    url: Optional[str] = None
    alt_text: Optional[str] = None
    is_primary: bool


@router.post("/projects/{project_id}/materials/{material_id}/image", response_model=ImageResponse, status_code=201)
async def upload_material_image(
    project_id: uuid.UUID,
    material_id: uuid.UUID,
    file: UploadFile = File(...),
    alt_text: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    service = ImageService(db)
    try:
        content = await file.read()
        image_asset = await service.upload_material_image(
            project_id=project_id,
            material_id=material_id,
            content=content,
            filename=file.filename or "image",
            alt_text=alt_text,
        )
        # Generate URL for the image
        url = f"/projects/{project_id}/images/{image_asset.id}"
        return ImageResponse(
            id=image_asset.id,
            project_id=image_asset.project_id,
            owner_type=image_asset.owner_type,
            owner_id=image_asset.owner_id,
            storage_backend=image_asset.storage_backend,
            storage_key=image_asset.storage_key,
            mime_type=image_asset.mime_type,
            url=url,
            alt_text=image_asset.alt_text,
            is_primary=image_asset.is_primary,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/projects/{project_id}/recipes/{recipe_id}/image", response_model=ImageResponse, status_code=201)
async def upload_recipe_image(
    project_id: uuid.UUID,
    recipe_id: uuid.UUID,
    file: UploadFile = File(...),
    alt_text: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    service = ImageService(db)
    try:
        content = await file.read()
        image_asset = await service.upload_recipe_image(
            project_id=project_id,
            recipe_id=recipe_id,
            content=content,
            filename=file.filename or "image",
            alt_text=alt_text,
        )
        # Generate URL for the image
        url = f"/projects/{project_id}/images/{image_asset.id}"
        return ImageResponse(
            id=image_asset.id,
            project_id=image_asset.project_id,
            owner_type=image_asset.owner_type,
            owner_id=image_asset.owner_id,
            storage_backend=image_asset.storage_backend,
            storage_key=image_asset.storage_key,
            mime_type=image_asset.mime_type,
            url=url,
            alt_text=image_asset.alt_text,
            is_primary=image_asset.is_primary,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/projects/{project_id}/materials/{material_id}/image", response_model=ImageResponse)
def get_material_image(project_id: uuid.UUID, material_id: uuid.UUID, db: Session = Depends(get_db)):
    service = ImageService(db)
    try:
        image_asset = service.get_material_image(project_id, material_id)
        if not image_asset:
            raise HTTPException(status_code=404, detail="Image not found")
        url = f"/projects/{project_id}/images/{image_asset.id}"
        return ImageResponse(
            id=image_asset.id,
            project_id=image_asset.project_id,
            owner_type=image_asset.owner_type,
            owner_id=image_asset.owner_id,
            storage_backend=image_asset.storage_backend,
            storage_key=image_asset.storage_key,
            mime_type=image_asset.mime_type,
            url=url,
            alt_text=image_asset.alt_text,
            is_primary=image_asset.is_primary,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/projects/{project_id}/recipes/{recipe_id}/image", response_model=ImageResponse)
def get_recipe_image(project_id: uuid.UUID, recipe_id: uuid.UUID, db: Session = Depends(get_db)):
    service = ImageService(db)
    try:
        image_asset = service.get_recipe_image(project_id, recipe_id)
        if not image_asset:
            raise HTTPException(status_code=404, detail="Image not found")
        url = f"/projects/{project_id}/images/{image_asset.id}"
        return ImageResponse(
            id=image_asset.id,
            project_id=image_asset.project_id,
            owner_type=image_asset.owner_type,
            owner_id=image_asset.owner_id,
            storage_backend=image_asset.storage_backend,
            storage_key=image_asset.storage_key,
            mime_type=image_asset.mime_type,
            url=url,
            alt_text=image_asset.alt_text,
            is_primary=image_asset.is_primary,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/projects/{project_id}/images/{image_asset_id}")
async def stream_image(project_id: uuid.UUID, image_asset_id: uuid.UUID, db: Session = Depends(get_db)):
    from fastapi.responses import StreamingResponse
    
    service = ImageService(db)
    try:
        image_asset = service.get_image_by_id(image_asset_id)
        if not image_asset or image_asset.project_id != project_id:
            raise HTTPException(status_code=404, detail="Image not found")
        
        stream = await service.get_image_stream(image_asset_id)
        
        return StreamingResponse(
            stream,
            media_type=image_asset.mime_type,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/projects/{project_id}/images/{image_asset_id}")
async def delete_image(project_id: uuid.UUID, image_asset_id: uuid.UUID, db: Session = Depends(get_db)):
    service = ImageService(db)
    try:
        image_asset = service.get_image_by_id(image_asset_id)
        if not image_asset or image_asset.project_id != project_id:
            raise HTTPException(status_code=404, detail="Image not found")
        
        await service.delete_image(image_asset_id)
        return {"message": "Image deleted"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
