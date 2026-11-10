# ResearchPilot AI

A multi-agent research assistant portfolio project. It coordinates four specialist agents to research a question, synthesize findings, check claims against retrieved sources, and produce a cited report.

## Architecture

```text
React UI -> FastAPI -> LangGraph workflow
                         |-> Research agent (Tavily web search)
                         |-> Analysis agent (Gemini)
                         |-> Fact-check agent (Gemini; source-grounded)
                         `-> Report agent (Gemini; cited Markdown)
```

The workflow keeps retrieved URLs and snippets in state and requires the report to cite source IDs (`[S1]`, `[S2]`). Fact checking is a source-grounded review, not a guarantee of truth. The app clearly labels that limitation.

## Run locally

Requirements: Python 3.11+, Node 20+, a Gemini API key, and a Tavily API key.

1. Copy `backend/.env.example` to `backend/.env` and add keys.
2. Start the API:
   ```bash
   cd backend
   python -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   uvicorn app.main:app --reload
   ```
3. Start the UI in another terminal:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
4. Open the Vite URL (normally http://localhost:5173). API docs: http://localhost:8000/docs.

If API keys are absent, the API returns a helpful configuration error rather than pretending to have performed live research.

## API

`POST /api/research` JSON body:
```json
{"question":"What are the latest practical uses of graph neural networks?","max_results":5}
```

`GET /health` checks service availability.

## Engineering extensions to pursue

- Add PostgreSQL persistence for research runs and user workspaces.
- Add pgvector semantic retrieval and deduplication.
- Add background jobs, retries, rate limits, and streaming progress.
- Add evaluation datasets for citation precision, claim support, and answer completeness.
- Add authentication, observability, and deployment.

## Portfolio proof points

Do not invent metrics. Benchmark latency, source relevance, citation coverage, and cost across a fixed evaluation set, then report measured results in the README.
