from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "textsummary" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "url" TEXT NOT NULL,
    "summary" TEXT NOT NULL,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS "token" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "access_token" VARCHAR(255) NOT NULL,
    "token_type" VARCHAR(50) NOT NULL
);
CREATE TABLE IF NOT EXISTS "tokendata" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "username" VARCHAR(50)
);
CREATE TABLE IF NOT EXISTS "user" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "username" VARCHAR(50) NOT NULL UNIQUE,
    "email" VARCHAR(100) NOT NULL UNIQUE,
    "full_name" VARCHAR(100),
    "disabled" BOOL NOT NULL DEFAULT False,
    "hashed_password" VARCHAR(255) NOT NULL
);
CREATE TABLE IF NOT EXISTS "pdfhighlight" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "doi" VARCHAR(255) NOT NULL,
    "highlight" JSONB NOT NULL,
    "comment" TEXT,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "user_id" INT NOT NULL REFERENCES "user" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(100) NOT NULL,
    "content" JSONB NOT NULL
);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """
