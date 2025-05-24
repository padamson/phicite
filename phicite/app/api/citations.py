from fastapi import APIRouter
from app.api import crud
from app.models.pydantic import HighlightPayloadSchema, HighlightResponseSchema

router = APIRouter()

@router.post("/", response_model=HighlightResponseSchema, status_code=201)
async def create_citation(payload: HighlightPayloadSchema) -> HighlightResponseSchema:
    citation_id = await crud.post_citation(payload)
    response_object = {"id": citation_id, "doi": payload.doi}
    return response_object