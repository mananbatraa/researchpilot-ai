from __future__ import annotations
import json
from typing import Any, Iterator
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from .config import settings
from .agents import workflow as live_workflow, STEPS
from .demo import DemoWorkflow, DEMO_DISCLAIMER

DISCLAIMER = "AI-generated research can be incomplete or incorrect. Verify important claims against the linked primary sources."

workflow = DemoWorkflow() if settings.demo_mode else live_workflow

app = FastAPI(title="ResearchPilot AI", version="0.2.0", description="A source-grounded multi-agent research assistant")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_origin_regex=settings.cors_origin_regex or None,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

class ResearchRequest(BaseModel):
    question: str = Field(min_length=12, max_length=1000)
    max_results: int = Field(default=5, ge=3, le=10)


def _require_keys() -> None:
    if settings.demo_mode:
        return
    missing = [name for name, value in (("GEMINI_API_KEY", settings.gemini_api_key), ("TAVILY_API_KEY", settings.tavily_api_key)) if not value]
    if missing:
        raise HTTPException(status_code=503, detail=f"Configure {', '.join(missing)} on the backend (backend/.env locally, or your host's environment variables) before running research.")


def _result(question: str, state: dict[str, Any]) -> dict[str, Any]:
    return {"question": question, "report": state.get("report", ""), "analysis": state.get("analysis", ""), "fact_check": state.get("fact_check", ""), "sources": state.get("sources", []), "disclaimer": DEMO_DISCLAIMER if settings.demo_mode else DISCLAIMER, "demo": settings.demo_mode}


@app.get("/health")
def health():
    return {"status": "ok", "service": "researchpilot-ai", "demo_mode": settings.demo_mode}


@app.post("/api/research")
def research(request: ResearchRequest):
    _require_keys()
    try:
        state = workflow.invoke({"question": request.question, "max_results": request.max_results})
        return _result(request.question, state)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Research workflow failed: {exc}") from exc


def _sse(event: str, data: dict[str, Any]) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


def _stream_research(request: ResearchRequest) -> Iterator[str]:
    state: dict[str, Any] = {"question": request.question, "max_results": request.max_results}
    current = STEPS[0]
    yield _sse("step", {"step": current, "status": "running"})
    try:
        for update in workflow.stream(state, stream_mode="updates"):
            for node, output in update.items():
                state.update(output or {})
                yield _sse("step", {"step": node, "status": "done", "output": output or {}})
                index = STEPS.index(node) + 1
                if index < len(STEPS):
                    current = STEPS[index]
                    yield _sse("step", {"step": current, "status": "running"})
        yield _sse("result", _result(request.question, state))
    except Exception as exc:
        yield _sse("error", {"step": current, "detail": f"Research workflow failed: {exc}"})


@app.post("/api/research/stream")
def research_stream(request: ResearchRequest):
    """Run the workflow and stream each agent's progress as Server-Sent Events.

    Events: `step` ({step, status: running|done, output?}), then `result` (same shape as
    POST /api/research) or `error` ({step, detail}).
    """
    _require_keys()
    return StreamingResponse(
        _stream_research(request),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
