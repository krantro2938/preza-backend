#!/usr/bin/env python3

# Запустить с помощью
# docker-compose exec fastapi python /app/populate_templates.py


import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "app"))

from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app.models import PresentationTemplate

def load_template_from_file(filepath: str) -> dict:
    """Load a template from a JSON file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def create_template(db: Session, title: str, slides: list, preview_url: str = None):
    db_template = PresentationTemplate(
        title=title,
        slides=slides,
        preview_url=preview_url
    )
    db.add(db_template)
    db.commit()
    db.refresh(db_template)
    return db_template

def main():
    template_data = load_template_from_file("prew-json/slide_template.json")

    simple_template = {
        "id": "simple_business_presentation",
        "title": "Simple Business Presentation",
        "slides": [
            {
                "id": "title_slide",
                "title": "Title Slide",
                "fields": [
                    {
                        "id": "title",
                        "type": "string",
                        "value": "Business Presentation"
                    },
                    {
                        "id": "subtitle",
                        "type": "string",
                        "value": "A simple overview"
                    }
                ]
            },
            {
                "id": "content_slide",
                "title": "Main Content",
                "fields": [
                    {
                        "id": "content",
                        "type": "string",
                        "value": "This is the main content of the presentation."
                    }
                ]
            },
            {
                "id": "conclusion_slide",
                "title": "Conclusion",
                "fields": [
                    {
                        "id": "conclusion",
                        "type": "string",
                        "value": "Thank you for your attention!"
                    }
                ]
            }
        ]
    }

    db = SessionLocal()

    try:
        disney_template = create_template(
            db=db,
            title=template_data["title"],
            slides=template_data["slides"],
            preview_url="https://example.com/disney-preview"
        )
        print(f"Created Disney template with ID: {disney_template.id}")

        simple_business_template = create_template(
            db=db,
            title=simple_template["title"],
            slides=simple_template["slides"],
            preview_url="https://example.com/simple-preview"
        )
        print(f"Created Simple Business template with ID: {simple_business_template.id}")

        print("Templates populated successfully!")

    except Exception as e:
        print(f"Error populating templates: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()