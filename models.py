from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import uuid


class SlideCreate(BaseModel):
    slide_number: int
    title: str
    content: str
    image_url: Optional[str] = None
    image_alt: Optional[str] = None
    layout: str = "title-content"


class SlideResponse(BaseModel):
    id: uuid.UUID
    slide_number: int
    title: str
    content: str
    image_url: Optional[str] = None
    image_alt: Optional[str] = None
    layout: str
    created_at: datetime

    model_config = {"from_attributes": True}


class PresentationCreate(BaseModel):
    topic: str = Field(..., description="Тема презентации")
    slides_count: int = Field(default=5, ge=3, le=20, description="Количество слайдов")
    style: str = Field(default="minimal", description="Стиль презентации")


class PresentationResponse(BaseModel):
    id: uuid.UUID
    topic: str
    style: str
    slides_count: int
    created_at: datetime
    updated_at: datetime
    slides: List[SlideResponse]

    model_config = {"from_attributes": True}


class PresentationList(BaseModel):
    id: uuid.UUID
    topic: str
    style: str
    slides_count: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
