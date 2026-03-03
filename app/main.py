from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import async_session
from app.api.v1.router import api_router
from app.seed.seed_db import seed_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables and seed data on startup
    #async with engine.begin() as conn:
        #await conn.run_sync(Base.metadata.create_all)

    # I removed the create_all call from the lifespan function because changes in the schema should be handled 
    # via Alembic migrations, not by automatically recreating tables on startup, create_all can change the schema
    # and bypass migration history. This prevents accidental data loss in a production environment. 

    async with async_session() as session:
        await seed_database(session)

    yield


app = FastAPI(
    title="Recipe Sharing API",
    description="A recipe sharing platform API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    # In production, you should specify allowed origins instead of allowing all. you can use the app settings
    # in order to set different allowed origins for dev, stg, and prod
    allow_origins=getattr(settings, "cors_origins"),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)
