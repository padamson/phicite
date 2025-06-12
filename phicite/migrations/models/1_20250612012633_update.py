from tortoise import BaseDBAsyncClient

async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
    ALTER TABLE "user" ADD COLUMN IF NOT EXISTS "is_admin" BOOLEAN NOT NULL DEFAULT FALSE;
    """

async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
    ALTER TABLE "user" DROP COLUMN IF EXISTS "is_admin";
    """
