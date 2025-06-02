
from fastapi import APIRouter, HTTPException, Path
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
async def read_citation(id: int = Path(..., gt=0)) -> PDFHighlight:
    citation = await crud.get_citation(id)
    if not citation:
        raise HTTPException(status_code=404, detail="Citation not found")
    return citation

@router.get("/", response_model=list[PDFHighlightSchema])
async def read_all_citations() -> list[PDFHighlight]:
    return await crud.get_all_citations()

@router.delete("/{id}/", response_model=HighlightResponseSchema)
async def delete_citation(id: int = Path(..., gt=0)) -> HighlightResponseSchema:
    citation = await crud.get_citation(id)
    if not citation:
        raise HTTPException(status_code=404, detail="Citation not found")
    
    await crud.delete_citation(id)
    return citation

@router.put("/{id}/", response_model=PDFHighlightSchema)
async def update_citation(payload: HighlightPayloadSchema, id: int = Path(..., gt=0)) -> HighlightResponseSchema:
    try:
        citation = await crud.put_citation(id, payload)
        if not citation:
            raise HTTPException(status_code=404, detail="Citation not found")
        return citation
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