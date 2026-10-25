"""
Automated Test Suite for FastAPI CORS Configuration and Preflight Handling.

Prompt 23 Verification:
- Explicit allowed production origins
- Disallowed origins
- Preflight OPTIONS requests
- Supported credential behavior
- Environment variable parsing (CORS_ORIGINS & BACKEND_CORS_ORIGINS, JSON arrays, quotes, slashes)
- Startup validation and separation of production vs development settings
"""
import pytest
from starlette.datastructures import Headers
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import PlainTextResponse

from app.core.config import Settings


@pytest.fixture(autouse=True)
def init_test_tables():
    """Override database table initialization for pure CORS/Config tests."""
    yield


@pytest.fixture(scope="session", autouse=True)
def use_sqlite():
    """Override session use_sqlite fixture."""
    yield


def test_default_cors_settings_valid():
    """Verify default CORS configuration is valid."""
    settings = Settings()
    settings.validate_cors_settings()
    origins = settings.cors_origins_list
    assert "https://patchura-frontend.onrender.com" in origins
    assert "http://localhost:5173" in origins
    assert "http://localhost:3000" in origins


def test_cors_origins_json_array_parsing():
    """Verify JSON array formatted string e.g. ['https://...'] is cleanly parsed."""
    settings = Settings(CORS_ORIGINS='["https://patchura-frontend.onrender.com"]')
    origins = settings.cors_origins_list
    assert "https://patchura-frontend.onrender.com" in origins
    assert not any("[" in o or "]" in o or '"' in o for o in origins)


def test_cors_origins_trailing_slashes_and_quotes():
    """Verify trailing slashes and quotation marks are automatically stripped."""
    settings = Settings(CORS_ORIGINS='"https://patchura-frontend.onrender.com/"')
    origins = settings.cors_origins_list
    assert "https://patchura-frontend.onrender.com" in origins
    assert not any(o.endswith("/") for o in origins)


def test_backend_cors_origins_fallback():
    """Verify BACKEND_CORS_ORIGINS variable is supported alongside CORS_ORIGINS."""
    settings = Settings(
        CORS_ORIGINS="",
        BACKEND_CORS_ORIGINS="https://partner-portal.example.com",
    )
    origins = settings.cors_origins_list
    assert "https://partner-portal.example.com" in origins


def test_production_mode_excludes_localhost():
    """Verify that in production mode, localhost origins are NOT included by default."""
    settings = Settings(
        APP_ENV="production",
        CORS_ORIGINS="https://patchura-frontend.onrender.com",
    )
    origins = settings.cors_origins_list
    assert "https://patchura-frontend.onrender.com" in origins
    assert "http://localhost:5173" not in origins
    assert "http://localhost:3000" not in origins
    assert "http://127.0.0.1:5173" not in origins


def test_production_mode_prohibits_wildcard_with_credentials():
    """Verify wildcard '*' cannot be combined with credentials in production."""
    settings = Settings(
        APP_ENV="production",
        CORS_ORIGINS="*",
        CORS_ALLOW_CREDENTIALS=True,
    )
    with pytest.raises(ValueError, match="CORS security violation"):
        settings.validate_cors_settings()


def test_invalid_origin_scheme_raises_error():
    """Verify origins without http:// or https:// raise a descriptive validation error."""
    settings = Settings(CORS_ORIGINS="ftp://invalid-server.com")
    with pytest.raises(ValueError, match="CORS configuration error"):
        settings.validate_cors_settings()


def test_cors_preflight_response_for_allowed_origin():
    """Verify preflight OPTIONS request returns 200 with credentials for allowed origin."""
    dummy_app = PlainTextResponse("ok")
    settings = Settings(CORS_ORIGINS="https://patchura-frontend.onrender.com")

    cors = CORSMiddleware(
        app=dummy_app,
        allow_origins=settings.cors_origins_list,
        allow_origin_regex=settings.cors_origin_regex,
        allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
        allow_methods=settings.CORS_ALLOW_METHODS,
        allow_headers=settings.CORS_ALLOW_HEADERS,
        expose_headers=settings.CORS_EXPOSE_HEADERS,
        max_age=settings.CORS_MAX_AGE,
    )

    headers = Headers({
        "origin": "https://patchura-frontend.onrender.com",
        "access-control-request-method": "POST",
        "access-control-request-headers": "content-type, authorization",
    })

    resp = cors.preflight_response(request_headers=headers)
    assert resp.status_code == 200
    assert resp.headers["access-control-allow-origin"] == "https://patchura-frontend.onrender.com"
    assert resp.headers["access-control-allow-credentials"] == "true"
    assert "POST" in resp.headers["access-control-allow-methods"]
    assert "content-type" in resp.headers["access-control-allow-headers"].lower()


def test_cors_preflight_response_for_disallowed_origin():
    """Verify preflight OPTIONS request returns 400 Disallowed CORS origin for untrusted origin."""
    dummy_app = PlainTextResponse("ok")
    settings = Settings(
        APP_ENV="production",
        CORS_ORIGINS="https://patchura-frontend.onrender.com",
    )

    cors = CORSMiddleware(
        app=dummy_app,
        allow_origins=settings.cors_origins_list,
        allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
        allow_methods=settings.CORS_ALLOW_METHODS,
        allow_headers=settings.CORS_ALLOW_HEADERS,
    )

    headers = Headers({
        "origin": "https://unauthorized-domain.com",
        "access-control-request-method": "POST",
    })

    resp = cors.preflight_response(request_headers=headers)
    assert resp.status_code == 400
    assert "Disallowed CORS origin" in resp.body.decode()


def test_cors_preflight_regex_matches_render_domains():
    """Verify preview or branch deployments on Render match regex without breaking."""
    dummy_app = PlainTextResponse("ok")
    settings = Settings(CORS_ORIGINS="https://patchura-frontend.onrender.com")

    cors = CORSMiddleware(
        app=dummy_app,
        allow_origins=settings.cors_origins_list,
        allow_origin_regex=settings.cors_origin_regex,
        allow_credentials=True,
    )

    preview_headers = Headers({
        "origin": "https://patchura-frontend-pr-42.onrender.com",
        "access-control-request-method": "GET",
    })

    resp = cors.preflight_response(request_headers=preview_headers)
    assert resp.status_code == 200
    assert resp.headers["access-control-allow-origin"] == "https://patchura-frontend-pr-42.onrender.com"
