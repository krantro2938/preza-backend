from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import models, schemas, database

router = APIRouter()

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