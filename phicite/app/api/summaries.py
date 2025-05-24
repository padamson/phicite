from typing import List

from fastapi import APIRouter, HTTPException, Path, BackgroundTasks

from app.summarizer import generate_summary
from app.api import crud
from app.models.pydantic import SummaryPayloadSchema, SummaryResponseSchema, SummaryUpdatePayloadSchema
from app.models.tortoise import SummarySchema, TextSummary


router = APIRouter()


@router.post("/", response_model=SummaryResponseSchema, status_code=201)
async def create_summary(payload: SummaryPayloadSchema, background_tasks: BackgroundTasks) -> SummaryResponseSchema:
    summary_id = await crud.post_summary(payload)

    background_tasks.add_task(generate_summary, summary_id, str(payload.url))

    response_object = {"id": summary_id, "url": payload.url}
    return response_object

@router.get("/{id}/", response_model=SummarySchema)
async def read_summary(id: int = Path(..., gt=0)) -> TextSummary:
    summary = await crud.get_summary(id)
    if not summary:
        raise HTTPException(status_code=404, detail="Summary not found")

    return summary

@router.get("/", response_model=List[SummarySchema])
async def read_all_summaries() -> List[TextSummary]:
    return await crud.get_all_summaries()


@router.delete("/{id}/", response_model=SummaryResponseSchema)
async def delete_summary(id: int = Path(..., gt=0)) -> SummaryResponseSchema:
    summary = await crud.get_summary(id)
    if not summary:
        raise HTTPException(status_code=404, detail="Summary not found")
    
    await crud.delete_summary(id)

    return summary

@router.put("/{id}/", response_model=SummarySchema)
async def update_summary(payload: SummaryUpdatePayloadSchema, id: int = Path(..., gt=0)) -> SummaryResponseSchema:
    summary = await crud.put_summary(id, payload)
    if not summary:
        raise HTTPException(status_code=404, detail="Summary not found")

    return summary