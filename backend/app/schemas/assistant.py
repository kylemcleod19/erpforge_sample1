from pydantic import BaseModel


class PageContext(BaseModel):
    current_page: str = ""
    page_data_summary: dict = {}


class ChatRequest(BaseModel):
    conversation_id: str | None = None
    message: str
    page_context: PageContext | None = None
