from typing import Annotated
import zxcvbn
from pydantic import BaseModel, AnyHttpUrl, AfterValidator, EmailStr
import re
from app.models.tortoise import User as UserDB, Token as TokenDB, TokenData as TokenDataDB
from tortoise.contrib.pydantic import pydantic_model_creator

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
    if not bool(re.match(doi_pattern, doi)):
        raise ValueError("Invalid DOI format")
    return doi


class HighlightPayloadSchema(BaseModel):
    doi: Annotated[str, AfterValidator(is_valid_doi)]
    highlight: dict
    comment: str | None = None

class HighlightDeleteResponseSchema(BaseModel):
    id: int

class HighlightCreateResponseSchema(BaseModel):
    id: int
    doi: str
    created_at: str

class HighlightResponseSchemaPublic(HighlightCreateResponseSchema):
    highlight: dict
    comment: str | None = None

class HighlightResponseSchema(HighlightResponseSchemaPublic):
    username: str

UserSchema = pydantic_model_creator(
    UserDB, 
    name="User",
    exclude=("hashed_password",)
)

UserInDBSchema = pydantic_model_creator(
    UserDB, 
    name="UserInDB"
)

def validate_password_strength(password: str) -> str:
    """
    Validate password strength using zxcvbn.
    Returns the password if it's strong enough, otherwise raises ValueError.
    """
    result = zxcvbn.zxcvbn(password)
    
    # Scores range from 0-4, with 4 being strongest
    if result['score'] < 3:
        suggestions = result.get('feedback', {}).get('suggestions', [])
        warning = result.get('feedback', {}).get('warning', '')
        
        message = f"Password is too weak. {warning}"
        if suggestions:
            message += f" Suggestions: {', '.join(suggestions)}"
        
        raise ValueError(message)
    
    return password

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    full_name: str | None = None
    password: Annotated[str, AfterValidator(validate_password_strength)]

class AuthenticationPayloadSchema(BaseModel):
    username: str
    password: str

TokenSchema = pydantic_model_creator(
    TokenDB, 
    name="Token",
    exclude=("id",)
)

TokenDataSchema = pydantic_model_creator(
    TokenDataDB,
    name="TokenData",
    exclude=("id",)
)