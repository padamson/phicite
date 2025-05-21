from typing import Annotated
from pydantic import BaseModel, AnyHttpUrl, AfterValidator
import re

class SummaryPayloadSchema(BaseModel):
    url: AnyHttpUrl

class SummaryResponseSchema(SummaryPayloadSchema):
    id: int

class SummaryUpdatePayloadSchema(SummaryPayloadSchema):
    summary: str

def is_valid_doi(doi: str) -> str:
    doi = doi.lower()
    if doi.startswith("doi:"):
        doi = doi[4:]
    elif doi.startswith("https://doi.org/"):
        doi = doi[16:]
    doi_pattern = r"^10\.\d{4,9}/[-._;()/:A-Za-z0-9]+$"
    if bool(re.match(doi_pattern, doi)):
        return doi
    raise ValueError("Invalid DOI format")


class DoiUrl(BaseModel):
    doi: Annotated[str, AfterValidator(is_valid_doi)]