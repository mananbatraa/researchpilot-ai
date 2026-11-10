import { useState } from 'react';
import ReactMarkdown from 'react-markdown';

type Result = { report: string; analysis: string; fact_check: string; sources: {id:string; title:string; url:string; content:string}[]; disclaimer: string };
const API = 'http://localhost:8000';

export default function App() {
  const [question, setQuestion] = useState('How are multi-agent AI systems being used in software engineering, and what are their limitations?');
  const [result, setResult] = useState<Result | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  async function runResearch(e: React.FormEvent) {
    e.preventDefault(); setLoading(true); setError(''); setResult(null);
    try {
      const response = await fetch(`${API}/api/research`, { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({question, max_results: 5}) });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Research request failed');
      setResult(data);
    } catch (err) { setError(err instanceof Error ? err.message : 'Something went wrong'); }
    finally { setLoading(false); }
  }
  return <main className="shell">
    <nav><div className="brand"><span className="brandmark">R</span> ResearchPilot <span className="tag">AI RESEARCH WORKSPACE</span></div><span className="status"><i/> Multi-agent workflow</span></nav>
    <section className="hero"><p className="eyebrow">FROM QUESTION TO EVIDENCE</p><h1>Research, with a team<br/>of AI specialists.</h1><p className="sub">A research agent gathers sources. Analysts synthesize the evidence. A fact-checker challenges the findings. One report brings it together.</p></section>
    <form className="prompt" onSubmit={runResearch}><label htmlFor="question">WHAT SHOULD WE INVESTIGATE?</label><textarea id="question" value={question} onChange={e=>setQuestion(e.target.value)} minLength={12} maxLength={1000}/><div className="formbottom"><span>Be specific. Reports include linked sources and evidence limitations.</span><button disabled={loading || question.trim().length < 12}>{loading ? 'Researching…' : 'Start research ↗'}</button></div></form>
    {loading && <div className="loading"><div className="spinner"/><div><b>Agents are collaborating</b><p>Searching sources, analyzing evidence, checking claims and drafting your report.</p></div></div>}
    {error && <div className="error">{error}</div>}
    {result && <section className="results"><div className="resulthead"><div><p className="eyebrow">RESEARCH OUTPUT</p><h2>Your research brief</h2></div><span className="sourcecount">{result.sources.length} sources reviewed</span></div><article className="report"><ReactMarkdown>{result.report}</ReactMarkdown></article><div className="agents"><details><summary>Analysis agent output</summary><ReactMarkdown>{result.analysis}</ReactMarkdown></details><details><summary>Fact-check agent output</summary><ReactMarkdown>{result.fact_check}</ReactMarkdown></details></div><h3>Retrieved sources</h3><div className="sources">{result.sources.map(s=><a className="source" key={s.id} href={s.url} target="_blank" rel="noreferrer"><b>{s.id}</b><span>{s.title}<small>{s.url}</small></span>↗</a>)}</div><p className="disclaimer">{result.disclaimer}</p></section>}
    <footer>RESEARCHPILOT AI <span>Built with FastAPI · LangGraph · Gemini · Tavily · React</span></footer>
  </main>;
}
