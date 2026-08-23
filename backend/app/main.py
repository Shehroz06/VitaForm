from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.api.v1.router import api_v1_router
from app.config.settings import get_settings
from app.core.logging import configure_logging
from app.exceptions.handlers import register_exception_handlers
from app.middleware.request_id import RequestIdMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware


def create_app() -> FastAPI:
    configure_logging()
    settings = get_settings()

    app = FastAPI(title="AI Career Operating System API", version="0.1.0")

    # Middleware runs in reverse order of addition, so the last one added
    # here is the first to see an incoming request and the last to see the
    # response. RequestIdMiddleware is added last (truly outermost) so a
    # request id is assigned -- and available to every log line below it,
    # via the contextvar it sets -- before anything else, including a
    # TrustedHost rejection, runs.
    app.add_middleware(SecurityHeadersMiddleware, secure=settings.environment == "production")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        # Browsers hide every response header from JS except the CORS
        # safelist (Content-Type, Content-Length, etc.) unless the server
        # explicitly opts a custom header in -- without this, the resume
        # preview's X-Page-Count header (features/resumes/router.py) is
        # readable via curl but silently comes back null in the actual
        # frontend, since it's cross-origin (localhost:3000 -> :8000).
        expose_headers=["X-Page-Count", "X-Request-ID"],
    )
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_hosts)
    app.add_middleware(RequestIdMiddleware)

    register_exception_handlers(app)
    app.include_router(api_v1_router)

    return app


app = create_app()
