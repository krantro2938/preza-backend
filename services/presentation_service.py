from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from typing import List, Dict, Optional, Any
import uuid
import random

from database_models import Presentation, Slide
from models import PresentationResponse, PresentationList, SlideResponse


class PresentationService:
    
    async def create_presentation(
        self, 
        db: AsyncSession, 
        topic: str, 
        structure: Dict[str, Any], 
        images: Dict[int, Dict],
        slides_count: int,
        style: str
    ) -> PresentationResponse:
        """Создание новой презентации в базе данных"""
        
        # Generate randomized layout order for variety
        layout_types = ["image_left", "image_right", "text_only", "split_content", "image_top", "grid_layout"]
        layout_order = layout_types.copy()
        random.shuffle(layout_order)
        
        # Создаем презентацию
        presentation = Presentation(
            topic=topic,
            slides_count=slides_count,
            style=style,
            layout_order=layout_order
        )
        
        db.add(presentation)
        await db.flush()  # Получаем ID
        
        # Создаем слайды
        slides = []
        for slide_data in structure["slides"]:
            slide_number = slide_data["slide_number"]
            
            # Получаем изображение для слайда, если есть
            image_data = images.get(slide_number)
            image_url = image_data["url"] if image_data else None
            image_alt = image_data["alt_description"] if image_data else None
            
            slide = Slide(
                presentation_id=presentation.id,
                slide_number=slide_number,
                title=slide_data["title"],
                content=slide_data["content"],
                image_url=image_url,
                image_alt=image_alt,
                layout=slide_data.get("layout", "title-content")
            )
            
            slides.append(slide)
            db.add(slide)
        
        await db.commit()
        await db.refresh(presentation)
        
        # Загружаем слайды
        result = await db.execute(
            select(Presentation)
            .options(selectinload(Presentation.slides))
            .where(Presentation.id == presentation.id)
        )
        presentation_with_slides = result.scalar_one()
        
        return PresentationResponse.model_validate(presentation_with_slides)
    
    async def get_presentation(self, db: AsyncSession, presentation_id: uuid.UUID) -> Optional[PresentationResponse]:
        """Получение презентации по ID"""
        
        result = await db.execute(
            select(Presentation)
            .options(selectinload(Presentation.slides))
            .where(Presentation.id == presentation_id)
        )
        
        presentation = result.scalar_one_or_none()
        
        if not presentation:
            return None
        
        return PresentationResponse.model_validate(presentation)
    
    async def get_all_presentations(self, db: AsyncSession) -> List[PresentationList]:
        """Получение всех презентаций"""
        
        result = await db.execute(
            select(Presentation).order_by(Presentation.created_at.desc())
        )
        
        presentations = result.scalars().all()
        
        return [PresentationList.model_validate(p) for p in presentations]
    
    async def delete_presentation(self, db: AsyncSession, presentation_id: uuid.UUID) -> bool:
        """Удаление презентации"""
        
        # Сначала проверяем, существует ли презентация
        result = await db.execute(
            select(Presentation).where(Presentation.id == presentation_id)
        )
        
        presentation = result.scalar_one_or_none()
        
        if not presentation:
            return False
        
        # Удаляем презентацию (слайды удалятся каскадно)
        await db.delete(presentation)
        await db.commit()
        
        return True
    
    async def update_slide(
        self, 
        db: AsyncSession, 
        slide_id: uuid.UUID, 
        title: Optional[str] = None,
        content: Optional[str] = None,
        image_url: Optional[str] = None,
        image_alt: Optional[str] = None
    ) -> Optional[SlideResponse]:
        """Обновление слайда"""
        
        result = await db.execute(
            select(Slide).where(Slide.id == slide_id)
        )
        
        slide = result.scalar_one_or_none()
        
        if not slide:
            return None
        
        if title is not None:
            slide.title = title
        if content is not None:
            slide.content = content
        if image_url is not None:
            slide.image_url = image_url
        if image_alt is not None:
            slide.image_alt = image_alt
        
        await db.commit()
        await db.refresh(slide)
        
        return SlideResponse.model_validate(slide)
    
    async def reorder_slides(self, db: AsyncSession, new_order: List[Dict]) -> bool:
        """Изменение порядка слайдов"""
        try:
            # Update each slide's slide_number
            for item in new_order:
                slide_id = item['id']
                new_slide_number = item['slide_number']
                
                result = await db.execute(
                    select(Slide).where(Slide.id == slide_id)
                )
                slide = result.scalar_one_or_none()
                
                if slide:
                    slide.slide_number = new_slide_number
            
            await db.commit()
            return True
        except Exception as e:
            await db.rollback()
            print(f"Error reordering slides: {e}")
            return False
