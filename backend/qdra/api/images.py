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
    entity_id: Optional[uuid.UUID]
    storage_backend: str
    storage_key: str
    mime_type: str
    url: Optional[str] = None
    alt_text: Optional[str] = None
    is_primary: bool


def _make_response(image_asset, project_id: uuid.UUID) -> ImageResponse:
    return ImageResponse(
        id=image_asset.id,
        entity_id=image_asset.entity_id,
        storage_backend=image_asset.storage_backend,
        storage_key=image_asset.storage_key,
        mime_type=image_asset.mime_type,
        url=f"/projects/{project_id}/images/{image_asset.id}",
        alt_text=image_asset.alt_text,
        is_primary=image_asset.is_primary,
    )


@router.post("/projects/{project_id}/entities/{entity_id}/image", response_model=ImageResponse, status_code=201)
async def upload_entity_image(
    project_id: uuid.UUID,
    entity_id: uuid.UUID,
    file: UploadFile = File(...),
    alt_text: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    service = ImageService(db)
    try:
        content = await file.read()
        image_asset = await service.upload_entity_image(
            project_id=project_id,
            entity_id=entity_id,
            content=content,
            filename=file.filename or "image",
            alt_text=alt_text,
        )
        return _make_response(image_asset, project_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/projects/{project_id}/materials/{entity_id}/image", response_model=ImageResponse, status_code=201)
async def upload_material_image(
    project_id: uuid.UUID,
    entity_id: uuid.UUID,
    file: UploadFile = File(...),
    alt_text: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    service = ImageService(db)
    try:
        content = await file.read()
        image_asset = await service.upload_entity_image(
            project_id=project_id, entity_id=entity_id,
            content=content, filename=file.filename or "image", alt_text=alt_text,
        )
        return _make_response(image_asset, project_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/projects/{project_id}/recipes/{entity_id}/image", response_model=ImageResponse, status_code=201)
async def upload_recipe_image(
    project_id: uuid.UUID,
    entity_id: uuid.UUID,
    file: UploadFile = File(...),
    alt_text: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    service = ImageService(db)
    try:
        content = await file.read()
        image_asset = await service.upload_entity_image(
            project_id=project_id, entity_id=entity_id,
            content=content, filename=file.filename or "image", alt_text=alt_text,
        )
        return _make_response(image_asset, project_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/projects/{project_id}/entities/{entity_id}/image", response_model=ImageResponse)
def get_entity_image(project_id: uuid.UUID, entity_id: uuid.UUID, db: Session = Depends(get_db)):
    service = ImageService(db)
    image_asset = service.get_entity_image(entity_id)
    if not image_asset:
        raise HTTPException(status_code=404, detail="Image not found")
    return _make_response(image_asset, project_id)


@router.get("/projects/{project_id}/materials/{entity_id}/image", response_model=ImageResponse)
def get_material_image(project_id: uuid.UUID, entity_id: uuid.UUID, db: Session = Depends(get_db)):
    service = ImageService(db)
    image_asset = service.get_entity_image(entity_id)
    if not image_asset:
        raise HTTPException(status_code=404, detail="Image not found")
    return _make_response(image_asset, project_id)


@router.get("/projects/{project_id}/recipes/{entity_id}/image", response_model=ImageResponse)
def get_recipe_image(project_id: uuid.UUID, entity_id: uuid.UUID, db: Session = Depends(get_db)):
    service = ImageService(db)
    image_asset = service.get_entity_image(entity_id)
    if not image_asset:
        raise HTTPException(status_code=404, detail="Image not found")
    return _make_response(image_asset, project_id)


@router.get("/projects/{project_id}/images/{image_asset_id}")
async def stream_image(project_id: uuid.UUID, image_asset_id: uuid.UUID, db: Session = Depends(get_db)):
    from fastapi.responses import StreamingResponse
    
    service = ImageService(db)
    try:
        image_asset = service.get_image_by_id(image_asset_id)
        if not image_asset:
            raise HTTPException(status_code=404, detail="Image not found")
        # Derive project_id from entity
        entity = service.entity_repo.get_by_id(image_asset.entity_id)
        if not entity or entity.project_id != project_id:
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
        if not image_asset:
            raise HTTPException(status_code=404, detail="Image not found")
        # Derive project_id from entity
        entity = service.entity_repo.get_by_id(image_asset.entity_id)
        if not entity or entity.project_id != project_id:
            raise HTTPException(status_code=404, detail="Image not found")
        
        await service.delete_image(image_asset_id)
        return {"message": "Image deleted"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
