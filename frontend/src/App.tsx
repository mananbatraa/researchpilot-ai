import { useRef, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { DEMO_MODE, streamResearch, type Result, type Source, type StepName } from './api';

type StepStatus = 'pending' | 'running' | 'done' | 'error';
const STEPS: { id: StepName; label: string; running: string }[] = [
  { id: 'research', label: 'Search', running: 'Searching the web for sources…' },
  { id: 'analyze', label: 'Analyze', running: 'Synthesizing findings from the sources…' },
  { id: 'fact_check', label: 'Fact-check', running: 'Auditing each claim against the sources…' },
  { id: 'report', label: 'Write', running: 'Drafting the final report…' },
];
const idle = (): Record<StepName, StepStatus> => ({ research: 'pending', analyze: 'pending', fact_check: 'pending', report: 'pending' });

export default function App() {
  const [question, setQuestion] = useState('How are multi-agent AI systems being used in software engineering, and what are their limitations?');
  const [status, setStatus] = useState(idle);
  const [partial, setPartial] = useState<{ sources?: Source[]; analysis?: string; fact_check?: string }>({});
  const [result, setResult] = useState<Result | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const abortRef = useRef<AbortController | null>(null);

  async function runResearch(e: React.FormEvent) {
    e.preventDefault();
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;
    setLoading(true); setError(''); setResult(null); setPartial({}); setStatus(idle());
    try {
      await streamResearch(question, 5, {
        onStep: ({ step, status: s, output }) => {
          setStatus(prev => ({ ...prev, [step]: s }));
          if (output) setPartial(prev => ({ ...prev, ...output }));
        },
        onResult: setResult,
        onError: ({ step, detail }) => { setStatus(prev => ({ ...prev, [step]: 'error' })); setError(detail); },
      }, controller.signal);
    } catch (err) {
      if (!controller.signal.aborted) setError(err instanceof Error ? err.message : 'Something went wrong');
    } finally {
      if (abortRef.current === controller) setLoading(false);
    }
  }

  const started = loading || Object.values(status).some(s => s !== 'pending');
  const showProgress = started && !result;
  return <main className="shell">
    <nav><div className="brand"><span className="brandmark">R</span> ResearchPilot <span className="tag">AI RESEARCH WORKSPACE</span></div><span className="status"><i/> Multi-agent workflow</span></nav>
    <section className="hero"><p className="eyebrow">FROM QUESTION TO EVIDENCE</p><h1>Research, with a team<br/>of AI specialists.</h1><p className="sub">A research agent gathers sources. Analysts synthesize the evidence. A fact-checker challenges the findings. One report brings it together.</p></section>
    {(DEMO_MODE || result?.demo) && <div className="demobanner"><b>Demo mode</b> No API keys are used. Every question replays the same pre-recorded sample run so you can see how the agents work.</div>}
    <form className="prompt" onSubmit={runResearch}><label htmlFor="question">WHAT SHOULD WE INVESTIGATE?</label><textarea id="question" value={question} onChange={e=>setQuestion(e.target.value)} minLength={12} maxLength={1000}/><div className="formbottom"><span>Be specific. Reports include linked sources and evidence limitations.</span><button disabled={loading || question.trim().length < 12}>{loading ? 'Researching…' : 'Start research ↗'}</button></div></form>
    {started && <ol className="pipeline" aria-live="polite">{STEPS.map((step, i) => {
      const s = status[step.id];
      const note = s === 'running' ? step.running
        : s === 'done' ? (step.id === 'research' && partial.sources ? `${partial.sources.length} source${partial.sources.length === 1 ? "" : "s"} found` : 'Done')
        : s === 'error' ? 'Failed' : 'Waiting';
      return <li key={step.id} className={`step ${s}`}><span className="dot">{s === 'done' ? '✓' : s === 'error' ? '!' : s === 'running' ? <span className="spinner small"/> : i + 1}</span><div><b>{step.label}</b><small>{note}</small></div></li>;
    })}</ol>}
    {error && <div className="error">{error}</div>}
    {showProgress && (partial.sources || partial.analysis || partial.fact_check) && <section className="results live">
      <div className="agents">
        {partial.analysis && <details open><summary>Analysis agent output</summary><ReactMarkdown>{partial.analysis}</ReactMarkdown></details>}
        {partial.fact_check && <details open><summary>Fact-check agent output</summary><ReactMarkdown>{partial.fact_check}</ReactMarkdown></details>}
      </div>
      {partial.sources && <><h3>Retrieved sources</h3><SourceList sources={partial.sources}/></>}
    </section>}
    {result && <section className="results"><div className="resulthead"><div><p className="eyebrow">RESEARCH OUTPUT</p><h2>Your research brief</h2></div><span className="sourcecount">{result.sources.length} sources reviewed</span></div><article className="report"><ReactMarkdown>{result.report}</ReactMarkdown></article><div className="agents"><details><summary>Analysis agent output</summary><ReactMarkdown>{result.analysis}</ReactMarkdown></details><details><summary>Fact-check agent output</summary><ReactMarkdown>{result.fact_check}</ReactMarkdown></details></div><h3>Retrieved sources</h3><SourceList sources={result.sources}/><p className="disclaimer">{result.disclaimer}</p></section>}
    <footer>RESEARCHPILOT AI <span>Built with FastAPI · LangGraph · Gemini · Tavily · React</span></footer>
  </main>;
}

function SourceList({ sources }: { sources: Source[] }) {
  return <div className="sources">{sources.map(s=><a className="source" key={s.id} href={s.url} target="_blank" rel="noreferrer"><b>{s.id}</b><span>{s.title}<small>{s.url}</small></span>↗</a>)}</div>;
}
