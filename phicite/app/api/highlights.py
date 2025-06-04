
from fastapi import APIRouter, HTTPException, Path
from app.api import crud
from app.models.pydantic import HighlightPayloadSchema, HighlightResponseSchema
from app.models.tortoise import PDFHighlightSchema, PDFHighlight

router = APIRouter()


@router.post("/", response_model=HighlightResponseSchema, status_code=201)
async def create_highlight(payload: HighlightPayloadSchema) -> HighlightResponseSchema:
    highlight_id = await crud.post_highlight(payload)
    response_object = {"id": highlight_id, "doi": payload.doi}
    return response_object

@router.get("/{id}/", response_model=PDFHighlightSchema)
async def read_highlight(id: int = Path(..., gt=0)) -> PDFHighlight:
    highlight = await crud.get_highlight(id)
    if not highlight:
        raise HTTPException(status_code=404, detail="highlight not found")
    return highlight

@router.get("/", response_model=list[PDFHighlightSchema])
async def read_all_highlights() -> list[PDFHighlight]:
    return await crud.get_all_highlights()

@router.delete("/{id}/", response_model=HighlightResponseSchema)
async def delete_highlight(id: int = Path(..., gt=0)) -> HighlightResponseSchema:
    highlight = await crud.get_highlight(id)
    if not highlight:
        raise HTTPException(status_code=404, detail="highlight not found")
    
    await crud.delete_highlight(id)
    return highlight

@router.put("/{id}/", response_model=PDFHighlightSchema)
async def update_highlight(payload: HighlightPayloadSchema, id: int = Path(..., gt=0)) -> HighlightResponseSchema:
    try:
        highlight = await crud.put_highlight(id, payload)
        if not highlight:
            raise HTTPException(status_code=404, detail="highlight not found")
        return highlight
    except ValueError as e:
        raise HTTPException(
            status_code=422,
            detail=[{
                "loc": ["body", "doi"],
                "msg": f"Value error, {str(e)}",
                "type": "value_error",
                "ctx": {"error": {}}
            }]
        )