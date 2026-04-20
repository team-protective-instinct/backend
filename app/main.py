import logging
from fastapi import FastAPI

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
from app.core.database import engine, Base
from app.models import User, Incident
from app.controllers import webhook_controller, user_controller

Base.metadata.create_all(bind=engine)

app = FastAPI()

# 컨트롤러의 라우터를 등록
app.include_router(webhook_controller.router)
app.include_router(user_controller.router)
