from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE INDEX IF NOT EXISTS "idx_pdfhighligh_doi_6d1149" ON "pdfhighlight" ("doi");"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP INDEX IF EXISTS "idx_pdfhighligh_doi_6d1149";"""
