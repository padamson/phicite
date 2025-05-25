from fastapi import APIRouter, HTTPException
from app.api import crud
from app.models.pydantic import HighlightPayloadSchema, HighlightResponseSchema
from app.models.tortoise import PDFHighlightSchema, PDFHighlight

router = APIRouter()

@router.post("/", response_model=HighlightResponseSchema, status_code=201)
async def create_citation(payload: HighlightPayloadSchema) -> HighlightResponseSchema:
    citation_id = await crud.post_citation(payload)
    response_object = {"id": citation_id, "doi": payload.doi}
    return response_object

@router.get("/{id}/", response_model=PDFHighlightSchema)
async def read_citation(id: int) -> PDFHighlight:
    citation = await crud.get_citation(id)
    if not citation:
        raise HTTPException(status_code=404, detail="Citation not found")
    return citation