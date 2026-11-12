from __future__ import annotations
from typing import TypedDict, Any
from langgraph.graph import StateGraph, END
from google import genai
from tavily import TavilyClient
from .config import settings

class ResearchState(TypedDict, total=False):
    question: str
    max_results: int
    sources: list[dict[str, str]]
    analysis: str
    fact_check: str
    report: str
    error: str


def _llm(prompt: str) -> str:
    client = genai.Client(api_key=settings.gemini_api_key)
    response = client.models.generate_content(model=settings.gemini_model, contents=prompt)
    return (response.text or "").strip()


def research_agent(state: ResearchState) -> dict[str, Any]:
    client = TavilyClient(api_key=settings.tavily_api_key)
    response = client.search(query=state["question"], max_results=state.get("max_results", 5), search_depth="advanced")
    sources = []
    for i, item in enumerate(response.get("results", []), start=1):
        sources.append({"id": f"S{i}", "title": item.get("title", "Untitled"), "url": item.get("url", ""), "content": item.get("content", "")})
    if not sources:
        raise RuntimeError("The search provider returned no sources. Try a more specific question.")
    return {"sources": sources}


def analysis_agent(state: ResearchState) -> dict[str, str]:
    source_text = "\n\n".join(f"[{s['id']}] {s['title']}\nURL: {s['url']}\nExtract: {s['content']}" for s in state["sources"])
    prompt = f"You are the analysis agent. Analyze the research question using ONLY the supplied source extracts. Separate supported findings, patterns, disagreements, and evidence gaps. Cite every factual point with source IDs like [S1]. Do not invent facts.\n\nQUESTION: {state['question']}\n\nSOURCES:\n{source_text}"
    return {"analysis": _llm(prompt)}


def fact_check_agent(state: ResearchState) -> dict[str, str]:
    source_text = "\n\n".join(f"[{s['id']}] {s['title']}\n{s['content']}" for s in state["sources"])
    prompt = f"You are a skeptical fact-checking agent. Audit the analysis against the source extracts. List claims as SUPPORTED, PARTIALLY SUPPORTED, or NOT ESTABLISHED. Flag contradictions, overclaims, and missing evidence. Do not use outside knowledge. Cite source IDs.\n\nQUESTION: {state['question']}\nANALYSIS:\n{state['analysis']}\n\nSOURCES:\n{source_text}"
    return {"fact_check": _llm(prompt)}


def report_agent(state: ResearchState) -> dict[str, str]:
    source_list = "\n".join(f"[{s['id']}] [{s['title']}]({s['url']})" for s in state["sources"])
    prompt = f"Write a clear, useful research report in Markdown. Include an executive summary, key findings, disagreements/limitations, and conclusion. Use source IDs inline and a Sources section using exactly these links. Never introduce claims not present in the analysis. Make uncertainty explicit.\n\nQUESTION: {state['question']}\nANALYSIS:\n{state['analysis']}\n\nFACT CHECK:\n{state['fact_check']}\n\nAVAILABLE SOURCES:\n{source_list}"
    return {"report": _llm(prompt)}


STEPS = ["research", "analyze", "fact_check", "report"]


def build_graph():
    graph = StateGraph(ResearchState)
    graph.add_node("research", research_agent)
    graph.add_node("analyze", analysis_agent)
    graph.add_node("fact_check", fact_check_agent)
    graph.add_node("report", report_agent)
    graph.set_entry_point("research")
    graph.add_edge("research", "analyze")
    graph.add_edge("analyze", "fact_check")
    graph.add_edge("fact_check", "report")
    graph.add_edge("report", END)
    return graph.compile()

workflow = build_graph()
