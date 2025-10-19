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

def pptx_to_json(path: str) -> dict:
    prs = Presentation(path)
    slides = []
    for slide in prs.slides:
        title = slide.shapes.title.text.strip() if slide.shapes.title and slide.shapes.title.has_text_frame else ""
        bullets = []
        for shape in slide.shapes:
            if getattr(shape, "has_text_frame", False) and shape is not slide.shapes.title:
                for p in shape.text_frame.paragraphs:
                    if (p.text or "").strip() and getattr(p, "level", 0) == 0:
                        bullets.append(p.text.strip())

        if bullets:
            slides.append({
                "id": "bullet",
                "fields": {
                    "1": {"value": {"type": "title", "content": title or "Раздел"}},
                    "2": {"value": {"type": "bullet", "content": bullets}}
                }
            })
        elif title:
            slides.append({"id": "title", "fields": {"title": {"value": title}}})

    return {"slides": slides}


def build_presentation_from_json(presentation_data: dict, title: str = "Presentation") -> str:

    prs = Presentation()
    prs.slide_width = Inches(13.33)
    prs.slide_height = Inches(7.5)

    for slide_item in presentation_data.get("slides", []):
        slide_id = slide_item.get("id")
        fields = slide_item.get("fields", {})

        if slide_id == "title":
            text = fields.get("title", {}).get("value", "")
            if text:
                layout = prs.slide_layouts[0]
                slide = prs.slides.add_slide(layout)
                if slide.shapes.title:
                    slide.shapes.title.text = str(text)

        elif slide_id == "bullet":
            for key in sorted(fields.keys()):
                field = fields[key]
                value = field.get("value", {})
                if isinstance(value, dict):
                    block_type = value.get("type")
                    content = value.get("content")

                    if block_type == "title" and isinstance(content, str):
                        layout = prs.slide_layouts[0]
                        slide = prs.slides.add_slide(layout)
                        if slide.shapes.title:
                            slide.shapes.title.text = content

                    elif block_type == "bullet" and isinstance(content, list):
                        layout = prs.slide_layouts[1]
                        slide = prs.slides.add_slide(layout)
                        if slide.shapes.title:
                            slide.shapes.title.text = "Содержание"
                        body = slide.placeholders[1]
                        text_frame = body.text_frame
                        text_frame.clear()
                        for i, item in enumerate(content):
                            p = text_frame.add_paragraph() if i > 0 else text_frame.paragraphs[0]
                            p.text = str(item)
                            p.level = 0

    if len(prs.slides) == 0:
        slide = prs.slides.add_slide(prs.slide_layouts[0])
        if slide.shapes.title:
            slide.shapes.title.text = title

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