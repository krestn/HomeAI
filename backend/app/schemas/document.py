from datetime import datetime
from pydantic import BaseModel


class DocumentMetadata(BaseModel):
    id: str
    original_name: str
    uploaded_at: datetime
    preview: str
    preview_url: str
