from pydantic import BaseModel
from typing import Optional, List, Any

class PresentationTemplateBase(BaseModel):
    title: Optional[str] = None
    slides: List[Any]

class PresentationTemplateCreate(PresentationTemplateBase):
    pass

class PresentationTemplate(PresentationTemplateBase):
    id: int

    class Config:
        from_attributes = True

class PresentationBase(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    presentation: Any
    generating: bool = False
    slides_count: Optional[int] = None
    presentation_url: Optional[str] = None
    presentation_template_id: Optional[int] = None

class PresentationCreate(PresentationBase):
    pass

class Presentation(PresentationBase):
    id: int

    class Config:
        from_attributes = True