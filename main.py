from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import uuid
import os
from contextlib import asynccontextmanager

from pydantic_settings import BaseSettings
from pydantic import field_validator

from database import get_db, init_db
from models import PresentationCreate, PresentationResponse, PresentationList, SlideUpdate, SlideResponse
from services.ai_service import AIService
from services.image_service import ImageService
from services.presentation_service import PresentationService
from services.pptx_service import PPTXService


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database
    await init_db()
    yield

class Settings(BaseSettings):
    database_url: str
    openrouter_api_key: str
    unsplash_access_key: str
    unsplash_application_id: str
    unsplash_secret_key: str
    BACKEND_CORS_ORIGINS: list[str] = []

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    def split_origins(cls, v):
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v

settings = Settings()

app = FastAPI(
    title="AI Presentation Builder",
    description="Minimalistic AI-powered presentation builder",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Services
ai_service = AIService()
image_service = ImageService()
presentation_service = PresentationService()
pptx_service = PPTXService()


@app.get("/")
async def root():
    return {"message": "AI Presentation Builder API"}


@app.post("/api/presentations", response_model=PresentationResponse)
async def create_presentation(
    presentation_data: PresentationCreate,
    db: AsyncSession = Depends(get_db)
):
    """Создать новую презентацию с помощью ИИ"""
    try:
        # Generate presentation structure using AI
        structure = await ai_service.generate_presentation_structure(
            topic=presentation_data.topic,
            slides_count=presentation_data.slides_count,
            style=presentation_data.style
        )
        
        # Generate images for slides
        images = await image_service.get_images_for_slides(structure["slides"])
        
        # Create presentation in database
        presentation = await presentation_service.create_presentation(
            db=db,
            topic=presentation_data.topic,
            structure=structure,
            images=images,
            slides_count=presentation_data.slides_count,
            style=presentation_data.style
        )
        
        return presentation
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка создания презентации: {str(e)}")


@app.get("/api/presentations", response_model=List[PresentationList])
async def get_all_presentations(db: AsyncSession = Depends(get_db)):
    """Получить все презентации"""
    presentations = await presentation_service.get_all_presentations(db)
    return presentations


@app.get("/api/presentations/{presentation_id}", response_model=PresentationResponse)
async def get_presentation(
    presentation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Получить презентацию по ID"""
    presentation = await presentation_service.get_presentation(db, presentation_id)
    if not presentation:
        raise HTTPException(status_code=404, detail="Презентация не найдена")
    return presentation


@app.delete("/api/presentations/{presentation_id}")
async def delete_presentation(
    presentation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Удалить презентацию"""
    success = await presentation_service.delete_presentation(db, presentation_id)
    if not success:
        raise HTTPException(status_code=404, detail="Презентация не найдена")
    return {"message": "Презентация удалена"}


@app.patch("/api/slides/{slide_id}", response_model=SlideResponse)
async def update_slide(
    slide_id: uuid.UUID,
    slide_update: SlideUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Обновить слайд"""
    updated_slide = await presentation_service.update_slide(
        db=db,
        slide_id=slide_id,
        title=slide_update.title,
        content=slide_update.content,
        image_url=slide_update.image_url,
        image_alt=slide_update.image_alt
    )
    
    if not updated_slide:
        raise HTTPException(status_code=404, detail="Слайд не найден")
    
    return updated_slide


@app.patch("/api/presentations/{presentation_id}/reorder")
async def reorder_slides(
    presentation_id: uuid.UUID,
    new_order: List[dict],  # [{"id": uuid, "slide_number": int}, ...]
    db: AsyncSession = Depends(get_db)
):
    """Изменить порядок слайдов"""
    try:
        success = await presentation_service.reorder_slides(db, new_order)
        if not success:
            raise HTTPException(status_code=400, detail="Не удалось изменить порядок")
        return {"message": "Порядок слайдов обновлен"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка: {str(e)}")


@app.get("/api/presentations/{presentation_id}/download/pptx")
async def download_presentation_pptx(
    presentation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Скачать презентацию в формате PPTX"""
    try:
        # Check if presentation exists
        presentation = await presentation_service.get_presentation(db, presentation_id)
        if not presentation:
            raise HTTPException(status_code=404, detail="Презентация не найдена")
        
        # Generate PPTX
        file_path = await pptx_service.export_to_pptx(db, presentation_id)
        
        # Create safe filename for download
        import urllib.parse
        safe_topic = presentation.topic.replace(' ', '_').replace('/', '_').replace('\\', '_')
        filename = f"{safe_topic}.pptx"
        
        # URL encode filename for Content-Disposition header to handle Cyrillic characters
        encoded_filename = urllib.parse.quote(filename.encode('utf-8'))
        
        return FileResponse(
            file_path,
            media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            filename=filename,
            headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"}
        )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка экспорта: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)