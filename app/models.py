from sqlalchemy import Column, Integer, String, Text, Boolean, JSON, ForeignKey
from .database import Base

class PresentationTemplate(Base):
    __tablename__ = "presentation_template"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(256))
    slides = Column(JSON, nullable=False)

class Presentation(Base):
    __tablename__ = "presentation"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(256))
    description = Column(Text)
    presentation = Column(JSON, nullable=False)
    generating = Column(Boolean, default=False, nullable=False)
    slides_count = Column(Integer)
    presentation_url = Column(String(512))
    presentation_template_id = Column(
        Integer,
        ForeignKey("presentation_template.id", ondelete="SET NULL")
    )