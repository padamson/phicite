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

    def highlight_text(self):
        return " ".join([highlight["text"] for highlight in self.highlight.values()])

    def __str__(self):
        highlighted_text = self.highlight_text()
        if len(highlighted_text) >= 30:
            return f"{self.doi}: {highlighted_text[:30]}..."
        else:
            return f"{self.doi}: {highlighted_text}"

PDFHighlightSchema = pydantic_model_creator(PDFHighlight) 