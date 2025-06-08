
from fastapi import APIRouter, HTTPException, Path, Depends
from typing import Annotated
from app.api.users import get_current_active_user
from app.api import crud
from app.models.pydantic import (
    HighlightPayloadSchema, 
    HighlightCreateResponseSchema, 
    HighlightResponseSchemaPublic,
    HighlightResponseSchema,
    HighlightDeleteResponseSchema,
    UserSchema
)

router = APIRouter()


@router.post("/", response_model=HighlightCreateResponseSchema, status_code=201)
async def create_highlight(
    payload: HighlightPayloadSchema,
    current_user: Annotated[UserSchema, Depends(get_current_active_user)]
) -> HighlightCreateResponseSchema:
    id, created_at  = await crud.post_highlight(payload, current_user.id)
    response_object = {"id": id, "doi": payload.doi, "created_at": str(created_at)}
    return response_object

@router.get("/{id}/", response_model=HighlightResponseSchema)
async def read_highlight(
    current_user: Annotated[UserSchema, Depends(get_current_active_user)],
    id: int = Path(..., gt=0)
) -> HighlightResponseSchema:
    highlight = await crud.get_highlight(id)

    if not highlight:
        raise HTTPException(status_code=404, detail="highlight not found")
    
    return highlight

@router.get("/{id}/public", response_model=HighlightResponseSchemaPublic)
async def read_highlight_public(
    id: int = Path(..., gt=0)
) -> HighlightResponseSchemaPublic:
    response = await crud.get_highlight_public(id)

    if not response:
        raise HTTPException(status_code=404, detail="highlight not found")
    
    return response 

@router.get("/", response_model=list[HighlightResponseSchema])
async def read_all_highlights(current_user: Annotated[UserSchema, Depends(get_current_active_user)]) -> list[HighlightResponseSchema]:
    return await crud.get_all_highlights()

@router.get("/public", response_model=list[HighlightResponseSchemaPublic])
async def read_all_highlights_public() -> list[HighlightResponseSchemaPublic]:
    return await crud.get_all_highlights_public()

@router.delete("/{id}/", response_model=HighlightDeleteResponseSchema)
async def delete_highlight(
    current_user: Annotated[UserSchema, Depends(get_current_active_user)],
    id: int = Path(..., gt=0),
) -> HighlightDeleteResponseSchema:
    try:
        response = await crud.delete_highlight(id, current_user.id)
        if not response:
            raise HTTPException(status_code=404, detail="highlight not found")
        return response
    except ValueError as e:
        if "User does not own this highlight" in str(e):
            raise HTTPException(status_code=403, detail="Not authorized to delete this highlight")
        raise HTTPException(
            status_code=422,
            detail=[{
                "loc": ["body", "doi"],
                "msg": f"Value error, {str(e)}",
                "type": "value_error",
                "ctx": {"error": {}}
            }]
        )

@router.put("/{id}/", response_model=HighlightCreateResponseSchema)
async def update_highlight(
    payload: HighlightPayloadSchema,
    current_user: Annotated[UserSchema, Depends(get_current_active_user)],
    id: int = Path(..., gt=0),
) -> HighlightCreateResponseSchema:
    try:
        updated_highlight = await crud.put_highlight(id, payload, current_user.id)
        if not updated_highlight:
            raise HTTPException(status_code=404, detail="highlight not found")
        updated_highlight["created_at"] = str(updated_highlight["created_at"])
        return updated_highlight
    except ValueError as e:
        if "User does not own this highlight" in str(e):
            raise HTTPException(status_code=403, detail="Not authorized to update this highlight")
        raise HTTPException(
            status_code=422,
            detail=[{
                "loc": ["body", "doi"],
                "msg": f"Value error, {str(e)}",
                "type": "value_error",
                "ctx": {"error": {}}
            }]
        )