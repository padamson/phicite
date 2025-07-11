import os
from datetime import datetime, timedelta, timezone
from typing import Union, Annotated
import jwt
from jwt.exceptions import InvalidTokenError
from fastapi import APIRouter, HTTPException, Path, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from app import auth
from app.api import crud
from app.models.pydantic import (
    UserCreate,
    UserSchema,
    UserInDBSchema,
    TokenSchema,
    TokenDataSchema,
    AuthSchema
)
from app.auth import oauth2_scheme
import casbin

router = APIRouter()

enforcer = casbin.Enforcer("abac_model.conf", "abac_policy.csv")

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)])-> UserSchema:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, 
                             os.environ.get("JWT_SECRET_KEY"), 
                             algorithms=[os.environ.get("JWT_ALGORITHM")])
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenDataSchema(username=username)
    except InvalidTokenError:
        raise credentials_exception
    user = await crud.get_user_by_token_data(token_data)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: Annotated[UserSchema, Depends(get_current_user)],
)-> UserSchema:
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def get_authorized_active_user(resource: str, action: str)->AuthSchema:
    async def get_user_and_authorize(current_active_user: Annotated[UserSchema, Depends(get_current_active_user)]):
        print(f"User: {current_active_user}, is_admin: {current_active_user.is_admin}")
        print(f"Resource: {resource}, Action: {action}")
        result = enforcer.enforce(current_active_user, resource, action)
        print(f"Authorization result: {result}")
        if not result:
            raise HTTPException(status_code=403, detail="Forbidden")
        return AuthSchema(**current_active_user.model_dump(), authorized=True)
    return get_user_and_authorize

@router.post("/", response_model=UserSchema, status_code=201)
async def register_user(payload: UserCreate) -> UserSchema:
    try:
        new_user = await crud.post_user(payload)
        return new_user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/admin/username/{username}/", response_model=UserSchema)
async def get_user_info_by_username(
    current_authorization: Annotated[
        AuthSchema, Depends(get_authorized_active_user("/users/admin/username/", "GET"))
    ],
    username: str = Path(..., min_length=1),
) -> UserSchema:
    user = await crud.get_user_by_username(username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.delete("/admin/username/{username}/", response_model=dict)
async def delete_user_by_username(
    current_authorization: Annotated[
        AuthSchema, Depends(get_authorized_active_user("/users/admin/username/", "DELETE"))
    ],
    username: str = Path(..., min_length=1),
) -> UserSchema:
    return await crud.delete_user_in_db_by_username(username)


@router.get("/admin/email/{email}/", response_model=UserSchema)
async def get_user_info_by_email(
    current_authorization: Annotated[
        AuthSchema, Depends(get_authorized_active_user("/users/admin/email/", "GET"))
    ],
    email: str = Path(..., min_length=1),
) -> UserSchema:
    user = await crud.get_user_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/admin/id/{id}/", response_model=UserSchema)
async def get_user_info_by_id(
    current_authorization: Annotated[
        AuthSchema, Depends(get_authorized_active_user("/users/admin/id/", "GET"))
    ],
    id: int = Path(..., gt=0),
) -> UserSchema:
    user = await crud.get_user_by_id(id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


async def authenticate_user(
    username: str, password: str
) -> Union[UserInDBSchema, bool]:
    user = await crud.get_user_in_db_by_username(username)
    if not user:
        print(f"User {username} not found")
        return False
    if not auth.verify_password(password, user.hashed_password):
        print(f"Incorrect password for user {username}")
        return False
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        os.environ.get("JWT_SECRET_KEY"),
        algorithm=os.environ.get("JWT_ALGORITHM")
    )
    return encoded_jwt


@router.post("/token", response_model=TokenSchema)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> TokenSchema:
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES")))
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return TokenSchema(access_token=access_token, token_type="bearer")


@router.get("/me/", response_model=UserSchema)
async def read_users_me(
    current_authorized_user: Annotated[AuthSchema, Depends(get_authorized_active_user("/users/me/", "GET"))]
):
    return UserSchema(**current_authorized_user.model_dump(exclude=("authorized",)))


@router.get("/me/highlights/")
async def read_own_highlights(
    current_authorized_user: Annotated[
        AuthSchema, Depends(get_authorized_active_user("/users/me/highlights/", "GET"))
    ],
):
    highlights = await crud.get_user_highlights(current_authorized_user.id)
    return highlights