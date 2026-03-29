import logging
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from routes import admin, posts, tags, comments, search, favorites

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)-8s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.DATABASE == "internal_db":
        if not settings.INTERNAL_DB_URL:
            raise RuntimeError("INTERNAL_DB_URL must be set when DATABASE=internal_db")
        from db import init_pool, close_pool
        logger.info("Starting up with internal_db (local PostgreSQL)")
        await init_pool(settings.INTERNAL_DB_URL)
    else:
        logger.info("Starting up with Supabase database")
    yield
    if settings.DATABASE == "internal_db":
        from db import close_pool
        await close_pool()


app = FastAPI(
    title="Repos API",
    description="Converts GitHub repos into structured bilingual blog articles (Vietnamese + English)",
    version="1.0.0",
    lifespan=lifespan,
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    logger.info(f"→ {request.method} {request.url.path}")
    try:
        response = await call_next(request)
    except Exception as exc:
        logger.error(f"✗ {request.method} {request.url.path} — unhandled exception: {exc}", exc_info=True)
        raise
    ms = (time.time() - start) * 1000
    level = logging.WARNING if response.status_code >= 400 else logging.INFO
    logger.log(level, f"← {request.method} {request.url.path} {response.status_code} ({ms:.0f}ms)")
    return response


# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        "https://repos.crawlingrobo.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(admin.router)
app.include_router(posts.router)
app.include_router(tags.router)
app.include_router(comments.router)
app.include_router(search.router)
app.include_router(favorites.router)


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "Repos API", "database": settings.DATABASE}


@app.get("/")
async def root():
    return {
        "message": "Repos API",
        "version": "1.0.0",
        "docs": "/docs",
    }
