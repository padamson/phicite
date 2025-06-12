from tortoise import fields, models
from tortoise.contrib.pydantic import pydantic_model_creator


class TextSummary(models.Model):
    url = fields.TextField()
    summary = fields.TextField()
    created_at = fields.DatetimeField(auto_now_add=True)

    def __str__(self):
        return self.url
    
SummarySchema = pydantic_model_creator(TextSummary)

class PDFHighlight(models.Model):
    doi = fields.CharField(max_length=255)
    highlight = fields.JSONField()
    comment = fields.TextField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    user = fields.ForeignKeyField("models.User", related_name="pdf_highlights")

    def highlight_text(self):
        return " ".join([highlight["text"] for highlight in self.highlight.values()])

    def __str__(self):
        highlighted_text = self.highlight_text()
        if len(highlighted_text) >= 30:
            return f"{self.doi}: {highlighted_text[:30]}..."
        else:
            return f"{self.doi}: {highlighted_text}"

PDFHighlightSchema = pydantic_model_creator(
    PDFHighlight,
    include=["id", "doi", "highlight", "comment", "created_at", "user.username"]
    ) 

# Tortoise ORM model (single table)
class User(models.Model):
    username = fields.CharField(max_length=50, unique=True)
    email = fields.CharField(max_length=100, unique=True)
    full_name = fields.CharField(max_length=100, null=True)
    disabled = fields.BooleanField(default=False)
    hashed_password = fields.CharField(max_length=255)
    is_admin = fields.BooleanField(default=False)

    def __str__(self):
        return self.username
    
UserSchema = pydantic_model_creator(User, exclude=("hashed_password",))

class Token(models.Model):
    access_token = fields.CharField(max_length=255)
    token_type = fields.CharField(max_length=50)

    def __str__(self):
        return self.access_token

TokenSchema = pydantic_model_creator(Token, name="Token")

class TokenData(models.Model):
    username = fields.CharField(max_length=50, null=True)

    def __str__(self):
        return self.username if self.username else "No username"

TokenDataSchema = pydantic_model_creator(TokenData, name="TokenData")