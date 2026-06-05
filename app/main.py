import logging
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.core.container import Container
from app.core.exception_handlers import (
    http_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from app.controllers import (
    webhook_controller,
    incident_controller,
    playbook_controller,
    response_plan_controller,
    push_token_controller,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def create_app() -> FastAPI:
    container = Container()

    # Wiring
    container.wire(
        modules=[
            webhook_controller,
            incident_controller,
            playbook_controller,
            response_plan_controller,
            push_token_controller,
        ]
    )

    # Create tables
    db = container.db()
    db.create_database()

    app = FastAPI()
    app.state.container = container
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:8081",
            "http://127.0.0.1:8081",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routers
    app.include_router(webhook_controller.router)
    app.include_router(incident_controller.router)
    app.include_router(playbook_controller.router)
    app.include_router(response_plan_controller.router)
    app.include_router(push_token_controller.router)

    return app


app = create_app()
