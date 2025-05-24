from typing import Union, List

from app.models.pydantic import SummaryPayloadSchema, SummaryUpdatePayloadSchema, HighlightPayloadSchema
from app.models.tortoise import TextSummary, PDFHighlight


async def post(payload: SummaryPayloadSchema) -> int:
    summary = TextSummary(
        url=payload.url,
        summary="",
    )
    await summary.save()
    return summary.id


async def get(id: int) -> Union[dict, None]:
    summary = await TextSummary.filter(id=id).first().values()
    if summary:
        return summary
    return None

async def get_all() -> List:
    summaries = await TextSummary.all().values()
    return summaries

async def delete(id: int) -> int:
    summary = await TextSummary.filter(id=id).first().delete()
    return summary

async def put(id: int, payload: SummaryUpdatePayloadSchema) -> Union[dict, None]:
    summary = await TextSummary.filter(id=id).update(url=payload.url, summary=payload.summary)
    if summary:
        updated_summary = await TextSummary.filter(id=id).first().values()
        return updated_summary
    return None

async def post_citation(payload: HighlightPayloadSchema) -> int:
    citation = PDFHighlight(
        doi=payload.doi,
        highlight=payload.highlight,
        comment=payload.comment 
    )
    await citation.save()
    return citation.id