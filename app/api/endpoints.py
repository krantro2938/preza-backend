from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import models, schemas, database
import httpx
import os
import json
import secrets
from fastapi.responses import FileResponse
import tempfile
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN

router = APIRouter()

def read_system_prompt():
    with open("prompts/system.txt", "r", encoding="utf-8") as f:
        return f.read().strip()
    
def generate_presentation_uid():
    token = secrets.token_urlsafe(8)
    return f"pres_{token}"

@router.post("/templates/", response_model=schemas.PresentationTemplate)
def create_template(template: schemas.PresentationTemplateCreate, db: Session = Depends(database.get_db)):
    db_template = models.PresentationTemplate(**template.model_dump())
    db.add(db_template)
    db.commit()
    db.refresh(db_template)
    return db_template

@router.get("/templates/", response_model=list[schemas.PresentationTemplate])
def read_templates(skip: int = 0, limit: int = 100, db: Session = Depends(database.get_db)):
    return db.query(models.PresentationTemplate).offset(skip).limit(limit).all()

@router.post("/presentations/", response_model=schemas.Presentation)
def create_presentation(presentation: schemas.PresentationCreate, db: Session = Depends(database.get_db)):
    db_pres = models.Presentation(**presentation.model_dump())
    db.add(db_pres)
    db.commit()
    db.refresh(db_pres)
    return db_pres

@router.get("/presentations/", response_model=list[schemas.Presentation])
def read_presentations(skip: int = 0, limit: int = 100, db: Session = Depends(database.get_db)):
    return db.query(models.Presentation).offset(skip).limit(limit).all()

@router.post("/generate", response_model=schemas.Presentation)
async def generate_presentation(
    request: schemas.GenerateRequest,
    db: Session = Depends(database.get_db)
):

    template = db.query(models.PresentationTemplate).filter(
        models.PresentationTemplate.id == request.template_id
    ).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    system_prompt = read_system_prompt()

    user_prompt = f"""
        Название: {request.title}
        Описание: {request.description}
        Шаблон слайдов: {json.dumps(template.slides, ensure_ascii=False)}
            """.strip()

    api_key = os.getenv("OPENROUTER_API_KEY")
    model = os.getenv("OPENROUTER_MODEL", "mistralai/mixtral-8x7b-instruct")

    if not api_key:
        raise HTTPException(status_code=500, detail="OPENROUTER_API_KEY not set")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "http://localhost:8000",
        "X-Title": "Perio Backend",
    }

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.7
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            data = response.json()

            raw_content = data["choices"][0]["message"]["content"].strip()

            print("=== RAW MODEL OUTPUT ===")
            print(raw_content)
            print("=========================")

            if raw_content.startswith("```"):
                parts = raw_content.split("```", 2)
                if len(parts) >= 2:
                    raw_content = parts[1]
                    if raw_content.startswith("json"):
                        raw_content = raw_content[4:].strip()

            presentation_data = json.loads(raw_content)

            slides_count = len(presentation_data.get("slides", []))
            
            uid = generate_presentation_uid()
            base_pr_url = os.getenv("PRESENTATION_BASE_URL")
            full_url = f"{base_pr_url}/{uid}"

            db_presentation = models.Presentation(
                title=request.title,
                description=request.description,
                presentation=presentation_data,
                generating=True,
                slides_count=slides_count,
                presentation_template_id=request.template_id,
                presentation_url=full_url
            )
            db.add(db_presentation)
            db.commit()
            db.refresh(db_presentation)

            return db_presentation

        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=502, detail=f"OpenRouter error: {e.response.text}")
        except json.JSONDecodeError:
            raise HTTPException(status_code=502, detail="Invalid JSON from model")
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")

def build_presentation_from_json(presentation_data: dict, title: str = "Presentation") -> str:

    prs = Presentation()
    prs.slide_width = Inches(13.33)
    prs.slide_height = Inches(7.5)

    title_slide_layout = prs.slide_layouts[0]
    slide = prs.slides.add_slide(title_slide_layout)
    title_box = slide.shapes.title
    if title_box:
        title_box.text = title

    for slide_data in presentation_data.get("slides", []):
        slide_type = slide_data.get("type", "content")
        content = slide_data.get("content", "")

        if slide_type == "title":
            layout = prs.slide_layouts[1]
            slide = prs.slides.add_slide(layout)
            if slide.shapes.title:
                slide.shapes.title.text = str(content)
        elif slide_type == "bullet":
            layout = prs.slide_layouts[1]
            slide = prs.slides.add_slide(layout)
            title = slide.shapes.title
            body = slide.placeholders[1]
            if title:
                title.text = "Содержание"
            if isinstance(content, list):
                text_frame = body.text_frame
                for i, item in enumerate(content):
                    p = text_frame.add_paragraph() if i > 0 else text_frame.paragraphs[0]
                    p.text = str(item)
                    p.level = 0
        elif slide_type == "text" or slide_type == "content":
            layout = prs.slide_layouts[1]
            slide = prs.slides.add_slide(layout)
            if slide.shapes.title:
                slide.shapes.title.text = "Слайд"
            body = slide.placeholders[1]
            text_frame = body.text_frame
            text_frame.text = str(content)
        elif slide_type == "image" and isinstance(content, dict):
            layout = prs.slide_layouts[6]
            slide = prs.slides.add_slide(layout)
            img_url = content.get("url", "")
            # Загрузка изображения по URL — заглушка
            title_box = slide.shapes.title
            if title_box:
                title_box.text = "Изображение"
        else:
            layout = prs.slide_layouts[1]
            slide = prs.slides.add_slide(layout)
            if slide.shapes.title:
                slide.shapes.title.text = "Слайд"
            body = slide.placeholders[1]
            text_frame = body.text_frame
            text_frame.text = str(content)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pptx") as tmp:
        prs.save(tmp.name)
        return tmp.name

@router.get("/presentations/{presentation_id}/download")
async def download_presentation(presentation_id: int, db: Session = Depends(database.get_db)):
    db_pres = db.query(models.Presentation).filter(
        models.Presentation.id == presentation_id
    ).first()
    
    if not db_pres:
        raise HTTPException(status_code=404, detail="Presentation not found")

    if not db_pres.presentation:
        raise HTTPException(status_code=400, detail="Presentation data is empty")

    try:
        pptx_path = build_presentation_from_json(
            db_pres.presentation,
            title=db_pres.title or "Presentation"
        )

        filename = f"presentation_{presentation_id}.pptx"
        return FileResponse(
            path=pptx_path,
            filename=filename,
            media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate PPTX: {str(e)}")