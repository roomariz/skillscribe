from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
import logging
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from hermes_writer.api.errors import ApiError
from hermes_writer.api.routes.documents import router as documents_router
from hermes_writer.api.routes.config import router as config_router
from hermes_writer.api.routes.health import router as health_router
from hermes_writer.api.routes.profiles import router as profiles_router
from hermes_writer.api.routes.status import router as status_router
from hermes_writer.config.privacy_config import PrivacyConfigStore
from hermes_writer.api.schemas import ErrorEnvelope
from hermes_writer.config.settings import Settings
from hermes_writer.storage.document_store import DocumentStore
from hermes_writer.storage.file_store import LocalFileStore
from hermes_writer.storage.profile_store import ProfileStore


def create_app(settings: Settings | None = None) -> FastAPI:
    app_settings = settings or Settings.from_env()
    log_dir = Path("logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=getattr(logging, app_settings.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_dir / "app.log", encoding="utf-8"),
        ],
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        app_settings.validate_for_startup()
        store = LocalFileStore(app_settings.storage_root)
        store.initialize()
        profile_store = ProfileStore(app_settings.storage_root)
        document_store = DocumentStore(app_settings.storage_root)
        privacy_config = PrivacyConfigStore(
            app_settings.storage_root,
            default_mode=app_settings.default_privacy_mode,
        )
        app.state.settings = app_settings
        app.state.file_store = store
        app.state.profile_store = profile_store
        app.state.document_store = document_store
        app.state.privacy_config = privacy_config
        yield

    app = FastAPI(title="Hermes Writer API", version="1.0.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[app_settings.cors_origin],
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    @app.exception_handler(ApiError)
    async def api_error_handler(_: Request, exc: ApiError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorEnvelope.from_error(
                error_code=exc.error_code,
                message=exc.message,
                details=exc.details,
                recovery_hint=exc.recovery_hint,
            ).model_dump(mode="json", exclude_none=True),
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_error_handler(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        if exc.status_code == 404:
            error_code = "NOT_FOUND"
            message = "The requested resource was not found."
        elif exc.status_code == 405:
            error_code = "METHOD_NOT_ALLOWED"
            message = "The requested method is not allowed for this resource."
        else:
            error_code = "HTTP_ERROR"
            message = str(exc.detail)
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorEnvelope.from_error(
                error_code=error_code,
                message=message,
                details={"detail": exc.detail},
            ).model_dump(mode="json", exclude_none=True),
            headers=exc.headers,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content=ErrorEnvelope.from_error(
                error_code="INVALID_REQUEST",
                message="Request validation failed.",
                details={"errors": exc.errors()},
                recovery_hint="Check the request shape and field values.",
            ).model_dump(mode="json", exclude_none=True),
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
        logging.getLogger(__name__).exception("Unhandled API error at %s", request.url.path)
        return JSONResponse(
            status_code=500,
            content=ErrorEnvelope.from_error(
                error_code="INTERNAL_ERROR",
                message="An unexpected error occurred.",
                recovery_hint="Check backend logs for the request timestamp.",
            ).model_dump(mode="json", exclude_none=True),
        )

    app.include_router(health_router)
    app.include_router(status_router)
    app.include_router(config_router)
    app.include_router(profiles_router)
    app.include_router(documents_router)
    return app
