from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime

class MessageBase(BaseModel):
    role: str
    content: str
    visualization_data: Optional[Dict[str, Any]] = None

class MessageCreate(MessageBase):
    pass

class MessageResponse(MessageBase):
    id: str
    conversation_id: str
    created_at: datetime

    class Config:
        from_attributes = True

class ConversationBase(BaseModel):
    title: str

class ConversationCreate(ConversationBase):
    pass

class ConversationResponse(ConversationBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    messages: List[MessageResponse] = []

    class Config:
        from_attributes = True

class BookmarkCreate(BaseModel):
    message_id: str
    title: str

class BookmarkResponse(BaseModel):
    id: str
    user_id: str
    message_id: str
    title: str
    created_at: datetime

    class Config:
        from_attributes = True
