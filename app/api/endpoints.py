from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import models, schemas, database
import httpx
import os
import json
import secrets

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
            if raw_content.startswith("```"):
                parts = raw_content.split("```", 2)
                if len(parts) >= 2:
                    raw_content = parts[1]
                    if raw_content.startswith("json"):
                        raw_content = raw_content[4:].strip()

            presentation_data = json.loads(raw_content)

            slides_count = len(presentation_data.get("slides", []))

            db_presentation = models.Presentation(
                title=request.title,
                description=request.description,
                presentation=presentation_data,
                generating=True,
                slides_count=slides_count,
                presentation_template_id=request.template_id,
                presentation_url=None
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