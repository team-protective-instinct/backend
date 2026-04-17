from fastapi import FastAPI
from app.core.database import engine, Base
from app.models import User, Incident
from app.controllers import webhook_controller, user_controller

Base.metadata.create_all(bind=engine)

app = FastAPI()

# 컨트롤러의 라우터를 등록
app.include_router(webhook_controller.router)
app.include_router(user_controller.router)
