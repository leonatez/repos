import logging
import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from routes import admin, posts, tags, comments, search, favorites

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)-8s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("app")

app = FastAPI(
    title="AI GitHub Repo Digest API",
    description="Converts GitHub repos into structured bilingual blog articles (Vietnamese + English)",
    version="1.0.0",
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
    return {"status": "ok", "service": "AI GitHub Repo Digest API"}


@app.get("/")
async def root():
    return {
        "message": "AI GitHub Repo Digest API",
        "version": "1.0.0",
        "docs": "/docs",
    }
