from fastapi import FastAPI
from .api import endpoints
from .database import Base, engine
import os
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Perio Presentation Generator")

allowed_origins_str = os.getenv("CORS_ALLOWED_ORIGINS", "")
allowed_origins = [origin.strip() for origin in allowed_origins_str.split(',') if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(endpoints.router)