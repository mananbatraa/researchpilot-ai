from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from .config import settings
from .agents import workflow

app = FastAPI(title="ResearchPilot AI", version="0.1.0", description="A source-grounded multi-agent research assistant")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

class ResearchRequest(BaseModel):
    question: str = Field(min_length=12, max_length=1000)
    max_results: int = Field(default=5, ge=3, le=10)

@app.get("/health")
def health():
    return {"status": "ok", "service": "researchpilot-ai"}

@app.post("/api/research")
def research(request: ResearchRequest):
    missing = [name for name, value in (("GEMINI_API_KEY", settings.gemini_api_key), ("TAVILY_API_KEY", settings.tavily_api_key)) if not value]
    if missing:
        raise HTTPException(status_code=503, detail=f"Configure {', '.join(missing)} in backend/.env before running research.")
    try:
        result = workflow.invoke({"question": request.question, "max_results": request.max_results})
        return {"question": request.question, "report": result.get("report", ""), "analysis": result.get("analysis", ""), "fact_check": result.get("fact_check", ""), "sources": result.get("sources", []), "disclaimer": "AI-generated research can be incomplete or incorrect. Verify important claims against the linked primary sources."}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Research workflow failed: {exc}") from exc
