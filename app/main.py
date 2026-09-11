from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import auth, bulk, dashboard, results, scan
from app.core.config import settings
from app.db.session import init_db, seed_admin


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()  # create tables if they don't exist yet
    seed_admin()  # ensure an admin account exists (see ADMIN_EMAIL/ADMIN_PASSWORD in settings)
    yield


app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok", "service": settings.APP_NAME}


# Each router owns one URL prefix — add new routers here only, never edit
# an existing router file for someone else's feature.
app.include_router(auth.router)
app.include_router(scan.router)
app.include_router(bulk.router)
app.include_router(results.router)
app.include_router(dashboard.router)
