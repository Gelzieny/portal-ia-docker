import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.responses import RedirectResponse

from app.core import database, redis as redis_store
from app.core.config import settings
from app.middleware.logging_middleware import LoggingMiddleware
from app.middleware.rate_limit_middleware import RateLimitMiddleware
from app.middleware.security_headers_middleware import SecurityHeadersMiddleware
from app.services.migration_service import MigrationService
from app.routers import ai_models, audit, auth, benchmarking, docs, ideas, mcp, model_access, migrations, news, notifications, permissions, prompts, stats, user_prompts, users

logger = logging.getLogger("goia")
IS_PRODUCTION = settings.APP_ENV.lower() == "production"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await database.init_pool()
    await MigrationService.run_migrations()
    await redis_store.init_redis()
    logger.info("GO.IA API iniciada [%s]", settings.APP_ENV)
    yield
    await database.close_pool()
    await redis_store.close_redis()
    logger.info("GO.IA API encerrada")


app = FastAPI(
    title="GO.IA API",
    description="Plataforma Estadual de Inteligência Artificial — Estado de Goiás",
    version="0.1.0",
    lifespan=lifespan,
    docs_url=None if IS_PRODUCTION else "/docs",
    redoc_url=None if IS_PRODUCTION else "/redoc",
    openapi_url=None if IS_PRODUCTION else "/openapi.json",
    root_path=settings.APP_CONTEXT_PATH if settings.APP_CONTEXT_PATH else "",
)

# ── Middleware (ordem importa: primeiro adicionado = mais externo) ────────────
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(LoggingMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers (/api prefix aplicado aqui) ──────────────────────────────────────
app.include_router(audit.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(ai_models.router)
app.include_router(benchmarking.router)
app.include_router(prompts.router)
app.include_router(docs.router)
app.include_router(news.router)
app.include_router(notifications.router)
app.include_router(stats.router)
app.include_router(mcp.router)
app.include_router(user_prompts.router)
app.include_router(model_access.router)
app.include_router(permissions.router)
app.include_router(ideas.router)
app.include_router(ideas.roadmap_router)
app.include_router(ideas.admin_router)
app.include_router(migrations.router)


@app.get("/", include_in_schema=False)
async def redirect_to_docs():
  return RedirectResponse(url="/docs")


# ── Health ────────────────────────────────────────────────────────────────────
@app.get("/monitor", tags=["health"])
async def health():
    return {"status": "ok", "env": settings.APP_ENV}


# ── Global exception handler ─────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Erro não tratado: %s %s", request.method, request.url)
    return JSONResponse(status_code=500, content={"detail": "Erro interno do servidor"})
