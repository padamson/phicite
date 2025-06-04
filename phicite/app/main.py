import logging

from fastapi import FastAPI

from app.api import ping, summaries, highlights, users
from app.db import init_db


log = logging.getLogger("uvicorn")

def create_application() -> FastAPI:
    """
    Create and configure the FastAPI application.
    """
    application = FastAPI()
    application.include_router(ping.router)
    application.include_router(summaries.router, prefix="/summaries", tags=["summaries"])
    application.include_router(highlights.router, prefix="/highlights", tags=["highlights"])
    application.include_router(users.router, prefix="/users", tags=["users"])

    return application

app = create_application()

init_db(app)