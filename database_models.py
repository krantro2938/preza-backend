import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, DateTime, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from database import Base


class Presentation(Base):
    __tablename__ = "presentations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    topic = Column(Text, nullable=False)
    style = Column(String(100), default="minimal")
    slides_count = Column(Integer, default=5)
    layout_order = Column(JSON, nullable=True)  # Randomized order of slide layouts
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship to slides
    slides = relationship("Slide", back_populates="presentation", cascade="all, delete-orphan")


class Slide(Base):
    __tablename__ = "slides"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    presentation_id = Column(UUID(as_uuid=True), ForeignKey("presentations.id"), nullable=False)
    slide_number = Column(Integer, nullable=False)
    title = Column(String(200), nullable=False)
    content = Column(Text)
    image_url = Column(String(500))
    image_alt = Column(String(200))
    layout = Column(String(50), default="title-content")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship to presentation
    presentation = relationship("Presentation", back_populates="slides")