from typing import Optional
from fastapi import FastAPI, Request, HTTPException
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import uvicorn

import memory_agents as agents

app = FastAPI(title="Yaad | 6-Day Memory Continuity & Multimodal Wellness Companion")
templates = Jinja2Templates(directory="templates")


class CheckinRequest(BaseModel):
    elder_name: str = "Dadi Maa (Kamala Devi)"
    todays_message: str
    image_base64: Optional[str] = None
    image_mime: Optional[str] = "image/jpeg"


@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")


@app.get("/api/memory-vault")
def api_get_vault():
    """Returns the current 6-day rolling memory window and Graphify context on page load."""
    return {
        "six_day_history": agents.load_six_day_vault(),
        "graphify_context": agents.load_graphify_context(),
        "logs": agents.get_recent_logs()
    }


@app.post("/api/reset-vault")
def api_reset_vault():
    """Resets the 6-day memory bank to the clean demo seed."""
    return {
        "status": "reset",
        "six_day_history": agents.reset_six_day_vault()
    }


@app.post("/api/checkin")
def api_run_checkin(req: CheckinRequest):
    try:
        if not agents.validate_environment():
            raise HTTPException(
                status_code=500,
                detail="GEMINI_API_KEY is missing or invalid in your .env file."
            )

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
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)