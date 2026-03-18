from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import os
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

from .config import settings
from .database import create_tables, SessionLocal
from .services.auth_service import create_default_admin
from .services.face_service import get_face_service
from .services import telegram_service
from .routers import auth, checkin, employees, attendance, devices, shifts


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    create_tables()
    db = SessionLocal()
    try:
        create_default_admin(db)
        face_svc = get_face_service()
        face_svc.reload_cache(db)
    finally:
        db.close()

    if settings.TELEGRAM_BOT_TOKEN:
        telegram_service.init_telegram(
            settings.TELEGRAM_BOT_TOKEN,
            settings.TELEGRAM_ADMIN_CHAT_ID or ""
        )

    yield
    # Shutdown (nothing to do)


app = FastAPI(
    title="ระบบสแกนหน้าเข้างาน",
    description="Face Recognition Attendance System",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_ORIGIN, "http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(checkin.router)
app.include_router(employees.router)
app.include_router(attendance.router)
app.include_router(devices.router)
app.include_router(shifts.router)

# Serve frontend static files
frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))
if os.path.exists(frontend_dir):
    app.mount("/js", StaticFiles(directory=os.path.join(frontend_dir, "js")), name="js")
    app.mount("/css", StaticFiles(directory=os.path.join(frontend_dir, "css")), name="css")
    app.mount("/admin", StaticFiles(directory=os.path.join(frontend_dir, "admin"), html=True), name="admin")

    @app.get("/")
    def serve_index():
        return FileResponse(
            os.path.join(frontend_dir, "index.html"),
            media_type="text/html; charset=utf-8"
        )
