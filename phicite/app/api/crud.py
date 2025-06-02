from typing import Union, List

from app.models.pydantic import (
    SummaryPayloadSchema,
    SummaryUpdatePayloadSchema,
    HighlightPayloadSchema,
    UserCreate,
    UserSchema
)
from app.models.tortoise import TextSummary, PDFHighlight, User as UserDB, UserSchema as UserDBSchema
from app.auth import get_password_hash

async def post_user(user: UserCreate) -> Union[dict, None]:
    """
    Register a new user in the database.
    
    Args:
        user: User data for registration
        
    Returns:
        The created user
        
    Raises:
        ValueError: If username or email already exists
    """
    # Check if username already exists
    existing_username = await UserDB.filter(username=user.username).first()
    if existing_username:
        raise ValueError(f"Username '{user.username}' already exists")
    
    # Check if email already exists
    existing_email = await UserDB.filter(email=user.email).first()
    if existing_email:
        raise ValueError(f"Email '{user.email}' already exists")
    
    # Hash the password
    hashed_password = get_password_hash(user.password)
    
    # Create the user
    user_obj = await UserDB.create(
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        hashed_password=hashed_password
    )
    
    return user_obj

async def get_user_by_username(username: str) -> Union[dict, None]:
    """
    Retrieve a user by username.
    
    Args:
        username: The username of the user to retrieve
        
    Returns:
        The user if found, otherwise None
    """
    user = await UserDB.filter(username=username).first()
    if user:
        return user
    return None

async def get_user_by_email(email: str) -> Union[dict, None]:
    """
    Retrieve a user by email.
    
    Args:
        email: The email of the user to retrieve
        
    Returns:
        The user if found, otherwise None
    """
    user = await UserDB.filter(email=email).first()
    if user:
        return user
    return None

async def get_user_by_id(id: int) -> Union[dict, None]:
    """
    Retrieve a user by id.
    
    Args:
        id: The id of the user to retrieve
        
    Returns:
        The user if found, otherwise None
    """
    user = await UserDB.filter(id=id).first()
    if user:
        return user
    return None

async def post_summary(payload: SummaryPayloadSchema) -> int:
    summary = TextSummary(
        url=payload.url,
        summary="",
    )
    await summary.save()
    return summary.id


async def get_summary(id: int) -> Union[dict, None]:
    summary = await TextSummary.filter(id=id).first().values()
    if summary:
        return summary
    return None

async def get_all_summaries() -> List:
    summaries = await TextSummary.all().values()
    return summaries

async def delete_summary(id: int) -> int:
    summary = await TextSummary.filter(id=id).first().delete()
    return summary

async def put_summary(id: int, payload: SummaryUpdatePayloadSchema) -> Union[dict, None]:
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

async def get_citation(id: int) -> Union[dict, None]:
    citation = await PDFHighlight.filter(id=id).first().values()
    if citation:
        return citation
    return None

async def get_all_citations() -> List:
    citations = await PDFHighlight.all().values()
    return citations

async def delete_citation(id: int) -> int:
    citation = await PDFHighlight.filter(id=id).first().delete()
    return citation

async def put_citation(id: int, payload: HighlightPayloadSchema) -> Union[dict, None]:
    existing_citation = await PDFHighlight.filter(id=id).first().values()
    
    if not existing_citation:
        return None
        
    if existing_citation["doi"] != payload.doi:
        raise ValueError("DOI does not match existing citation")
    
    citation = await PDFHighlight.filter(id=id).update(
        doi=payload.doi, 
        highlight=payload.highlight, 
        comment=payload.comment
    )
    
    if citation:
        updated_citation = await PDFHighlight.filter(id=id).first().values()
        return updated_citation
    return None