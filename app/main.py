import logging
from fastapi import FastAPI
from app.core.container import Container
from app.controllers import webhook_controller, user_controller, incident_controller

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def create_app() -> FastAPI:
    container = Container()
    
    # Wiring
    container.wire(modules=[
        webhook_controller,
        user_controller,
        incident_controller,
    ])

    # Create tables
    db = container.db()
    db.create_database()

    app = FastAPI()
    app.container = container  # type: ignore

    # Register routers
    app.include_router(webhook_controller.router)
    app.include_router(user_controller.router)
    app.include_router(incident_controller.router)

    return app


app = create_app()
