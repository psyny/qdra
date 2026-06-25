import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from db.session import get_db
from services.image_service import ImageService
from infrastructure.security.permission_checker import get_current_user_id, require_can_edit_material, require_can_edit_recipe
from repositories.project_template_repository import ProjectTemplateRepository
from repositories.project_repository import ProjectRepository
from repositories.entity_repository import EntityRepository

router = APIRouter(prefix="/api")


def _is_material_entity(entity_id: uuid.UUID, db: Session) -> bool:
    """Check if an existing entity is a material kind."""
    entity_repo = EntityRepository(db)
    entity = entity_repo.get_by_id(entity_id)
    if not entity:
        return False
    project = ProjectRepository(db).get_by_id(entity.project_id)
    if not project:
        return False
    entity_types = ProjectTemplateRepository(db).list_entity_types(
        project.project_template_id, kind="material"
    )
    return any(et.id == entity.entity_type_id for et in entity_types)


def _check_entity_edit_permission(
    entity_id: uuid.UUID,
    user_id: uuid.UUID,
    db: Session
) -> None:
    """Check if user has edit permission for the entity (material or recipe)."""
    entity_repo = EntityRepository(db)
    entity = entity_repo.get_by_id(entity_id)
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    
    is_material = _is_material_entity(entity_id, db)
    
    if is_material:
        # Check material edit permission
        user_service = __import__('services.user_service', fromlist=['UserService']).UserService(db)
        permissions = user_service.get_project_permissions(user_id, entity.project_id)
        if not permissions or not permissions.can_edit_material:
            raise HTTPException(status_code=403, detail="Permission 'can_edit_material' is required")
    else:
        # Check recipe edit permission
        user_service = __import__('services.user_service', fromlist=['UserService']).UserService(db)
        permissions = user_service.get_project_permissions(user_id, entity.project_id)
        if not permissions or not permissions.can_edit_recipe:
            raise HTTPException(status_code=403, detail="Permission 'can_edit_recipe' is required")


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
    width: Optional[int] = None
    height: Optional[int] = None


class PresignUploadRequest(BaseModel):
    filename: str
    mime_type: str
    file_size_bytes: int
    width: int
    height: int
    alt_text: Optional[str] = None


class PresignUploadResponse(BaseModel):
    image_asset_id: uuid.UUID
    upload_url: str
    storage_key: str
    required_method: str
    required_headers: dict


class FinalizeResponse(BaseModel):
    id: uuid.UUID
    entity_id: uuid.UUID
    mime_type: str
    width: int
    height: int
    url: str


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
        width=image_asset.width,
        height=image_asset.height,
    )


@router.post("/entities/{entity_id}/images/presign-upload", response_model=PresignUploadResponse, status_code=201)
async def presign_upload(
    entity_id: uuid.UUID,
    request: PresignUploadRequest,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Create a presigned URL for uploading an image."""
    # Check edit permission for the entity
    _check_entity_edit_permission(entity_id, user_id, db)
    
    service = ImageService(db)
    try:
        result = await service.presign_upload(
            entity_id=entity_id,
            filename=request.filename,
            mime_type=request.mime_type,
            file_size_bytes=request.file_size_bytes,
            width=request.width,
            height=request.height,
            alt_text=request.alt_text,
        )
        return PresignUploadResponse(
            image_asset_id=result["image_asset_id"],
            upload_url=result["upload_url"],
            storage_key=result["storage_key"],
            required_method="PUT",
            required_headers={"Content-Type": request.mime_type},
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/image-assets/{image_asset_id}/finalize", response_model=FinalizeResponse)
async def finalize_upload(
    image_asset_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Finalize an image upload after the file is uploaded to storage."""
    service = ImageService(db)
    try:
        result = await service.finalize_upload(image_asset_id)
        # Check edit permission for the entity
        _check_entity_edit_permission(result["entity_id"], user_id, db)
        return FinalizeResponse(
            id=result["id"],
            entity_id=result["entity_id"],
            mime_type=result["mime_type"],
            width=result["width"],
            height=result["height"],
            url=result["url"],
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/entities/{entity_id}/images", response_model=list[ImageResponse])
async def get_entity_images(
    entity_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    """Get all images for an entity."""
    service = ImageService(db)
    images = service.get_entity_images(entity_id)
    return [_make_response(img, img.entity.project_id) for img in images]


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


@router.delete("/entities/{entity_id}/images", status_code=204)
async def delete_entity_image(
    entity_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    """Delete the image for an entity."""
    service = ImageService(db)
    try:
        # Get the entity's image
        images = service.image_asset_repo.get_by_entity_id(entity_id)
        for image in images:
            await service.delete_image(image.id)
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
