import os
import time
import logging
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from typing import Optional, Deque, Dict

from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator
import uvicorn

import memory_agents as agents

logger = logging.getLogger("YaadAI.Server")

# =====================================================================
# LIFESPAN & STARTUP VERIFICATION (PRODUCTION READINESS)
# =====================================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Initializing Yaad Production Service...")
    agents.load_six_day_vault()
    agents.load_graphify_context()
    if not agents.validate_environment():
        logger.warning("⚠️ GEMINI_API_KEY not configured yet. Check .env before running check-ins.")
    yield
    logger.info("🛑 Shutting down Yaad Service cleanly.")

app = FastAPI(
    title="Yaad | 6-Day Memory Continuity & Multimodal Wellness Companion",
    version="1.0.0",
    docs_url="/docs",
    lifespan=lifespan
)

templates = Jinja2Templates(directory="templates")

# =====================================================================
# SECURITY FEATURE 1: CORS & HTTP SECURITY HEADERS MIDDLEWARE
# =====================================================================
allowed_origins = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "*").split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

# Sliding-window rate limiter store: IP -> timestamps
RATE_LIMIT_MAX = int(os.getenv("RATE_LIMIT_PER_MINUTE", "20"))
_rate_buckets: Dict[str, Deque[float]] = defaultdict(deque)

@app.middleware("http")
async def security_and_rate_limit_middleware(request: Request, call_next):
    # Rate limit POST endpoints to prevent token exhaustion / DoS
    if request.method == "POST":
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        bucket = _rate_buckets[client_ip]
        while bucket and now - bucket[0] > 60.0:
            bucket.popleft()
        if len(bucket) >= RATE_LIMIT_MAX:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Rate limit exceeded. Please wait a moment before sending another check-in."}
            )
        bucket.append(now)

    response = await call_next(request)
    # OWASP Recommended Security Headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Cache-Control"] = "no-store"
    return response


# =====================================================================
# SECURITY FEATURE 2: STRICT INPUT VALIDATION & SANITIZATION
# =====================================================================
ALLOWED_IMAGE_MIMES = {"image/jpeg", "image/png", "image/webp"}
MAX_BASE64_LENGTH = 5_500_000  # ~4 MB max decoded image size

class CheckinRequest(BaseModel):
    elder_name: str = Field(default="Dadi Maa (Kamala Devi)", min_length=1, max_length=80)
    todays_message: str = Field(..., min_length=2, max_length=2000)
    image_base64: Optional[str] = Field(default=None)
    image_mime: Optional[str] = Field(default="image/jpeg")

    @field_validator("elder_name", "todays_message")
    @classmethod
    def sanitize_text(cls, v: str) -> str:
        cleaned = "".join(ch for ch in v if ch == "\n" or ch == "\t" or ord(ch) >= 32).strip()
        if not cleaned:
            raise ValueError("Text input cannot be empty.")
        return cleaned

    @field_validator("image_mime")
    @classmethod
    def validate_mime(cls, v: Optional[str]) -> str:
        if not v:
            return "image/jpeg"
        mime = v.lower().strip()
        if mime not in ALLOWED_IMAGE_MIMES:
            raise ValueError(f"Unsupported image format '{mime}'. Allowed: JPEG, PNG, WEBP.")
        return mime

    @field_validator("image_base64")
    @classmethod
    def validate_image_size(cls, v: Optional[str]) -> Optional[str]:
        if v and len(v) > MAX_BASE64_LENGTH:
            raise ValueError("Uploaded image exceeds the 4MB security limit.")
        return v


# =====================================================================
# ROUTES & PRODUCTION HEALTH PROBES
# =====================================================================
@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")


@app.get("/healthz")
def health_probe():
    """Production readiness & liveness probe for DigitalOcean / Cloudways."""
    api_configured = agents.validate_environment()
    vault = agents.load_six_day_vault()
    return {
        "status": "healthy" if api_configured else "degraded_missing_api_key",
        "service": "yaad-wellness-companion",
        "version": "1.0.0",
        "model_configured": agents._get_clean_env("GEMINI_MODEL", "gemma-3-27b-it"),
        "six_day_vault_entries": len(vault),
        "graphify_grounded": True,
        "timestamp": int(time.time())
    }


@app.get("/api/memory-vault")
def api_get_vault():
    return {
        "six_day_history": agents.load_six_day_vault(),
        "graphify_context": agents.load_graphify_context(),
        "logs": agents.get_recent_logs()
    }


@app.post("/api/reset-vault")
def api_reset_vault():
    return {
        "status": "reset",
        "six_day_history": agents.reset_six_day_vault()
    }


@app.post("/api/checkin")
def api_run_checkin(req: CheckinRequest):
    if not agents.validate_environment():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI engine credentials are not configured on the server."
        )
    try:
        result = agents.run_yaad_checkin_pipeline(
            elder_name=req.elder_name,
            todays_message=req.todays_message,
            image_base64=req.image_base64,
            image_mime=req.image_mime or "image/jpeg"
        )
        return {
            "status": "success",
            "model": agents._get_clean_env("GEMINI_MODEL", "gemma-3-27b-it"),
            "data": result
        }
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        # Log full details internally, return safe message externally (Zero Red Flags)
        logger.error(f"Check-in execution error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred while processing the wellness check-in."
        )


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)




