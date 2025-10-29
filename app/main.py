import logging
from fastapi import FastAPI
from app.core.config import settings
from app.core.logging_config import setup_logging
from app.api.data import analytics, cbr_data
from app.core.scheduler import init_scheduler
from starlette.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.db.session import engine
from app.models.models import Base
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):    # Startup logic
    async with engine.begin() as conn:# create db
        await conn.run_sync(Base.metadata.create_all)
        print(" Database tables created successfully (if not exist)")
    # --- Start scheduler here ---
    try:
        init_scheduler()
        print("Scheduler started successfully.")
    except Exception as e:
        print(f"Failed to start scheduler: {e}")

    yield  # Application runs here
    #Shutdown logic
    await engine.dispose()
    print(" Database connection closed.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Svoye Zhil'ye Analytics APIs",
    lifespan=lifespan
)

if settings.all_cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.all_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],

    )


# Routers
app.include_router(analytics.router, prefix=f"{settings.API_VERSION_STR}/analytics", tags=["Analytics"])
app.include_router(cbr_data.router, prefix=f"{settings.API_VERSION_STR}")


#.............................................................

#We will deploy both UI and Backend in one place

#................................................................



# Get absolute path to the frontend build directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_BUILD_DIR = os.path.abspath(os.path.join(BASE_DIR, "frontend", "build"))

# Serve React static files
app.mount("/static", StaticFiles(directory=os.path.join(FRONTEND_BUILD_DIR, "static")), name="static")
@app.get("/")
async def serve_react_frontend():
    index_path = os.path.join(FRONTEND_BUILD_DIR, "index.html")
    return FileResponse(index_path)