export type Source = { id: string; title: string; url: string; content: string };
export type Result = { question: string; report: string; analysis: string; fact_check: string; sources: Source[]; disclaimer: string; demo?: boolean };
export type StepName = 'research' | 'analyze' | 'fact_check' | 'report';
export type StepEvent = { step: StepName; status: 'running' | 'done'; output?: Partial<Result> };
export type ErrorEvent = { step: StepName; detail: string };

import { simulateResearch } from './demo/simulate';

/** VITE_DEMO_MODE=1 runs entirely in the browser with a canned sample: no backend, no API keys. */
export const DEMO_MODE = ['1', 'true'].includes((import.meta.env.VITE_DEMO_MODE || '').toLowerCase());

export const API_URL = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/+$/, '');

type Handlers = { onStep: (e: StepEvent) => void; onResult: (r: Result) => void; onError: (e: ErrorEvent) => void };

/** POSTs a question and reads the Server-Sent Events stream (EventSource can't POST, so we parse it by hand). */
export async function streamResearch(question: string, maxResults: number, handlers: Handlers, signal?: AbortSignal) {
  if (DEMO_MODE) return simulateResearch(handlers, signal);
  const response = await fetch(`${API_URL}/api/research/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'text/event-stream' },
    body: JSON.stringify({ question, max_results: maxResults }),
    signal,
  });
  if (!response.ok || !response.body) {
    const data = await response.json().catch(() => ({}));
    const detail = typeof data.detail === 'string' ? data.detail : Array.isArray(data.detail) ? data.detail.map((d: { msg: string }) => d.msg).join('; ') : '';
    throw new Error(detail || `Research request failed (${response.status})`);
  }
  const reader = response.body.pipeThrough(new TextDecoderStream()).getReader();
  let buffer = '';
  let finished = false;
  for (;;) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += value.replace(/\r\n/g, '\n');
    let boundary;
    while ((boundary = buffer.indexOf('\n\n')) !== -1) {
      const block = buffer.slice(0, boundary);
      buffer = buffer.slice(boundary + 2);
      let event = 'message';
      const data: string[] = [];
      for (const line of block.split('\n')) {
        if (line.startsWith('event:')) event = line.slice(6).trim();
        else if (line.startsWith('data:')) data.push(line.slice(5).trimStart());
      }
      if (!data.length) continue;
      const payload = JSON.parse(data.join('\n'));
      if (event === 'step') handlers.onStep(payload);
      else if (event === 'result') { finished = true; handlers.onResult(payload); }
      else if (event === 'error') { finished = true; handlers.onError(payload); }
    }
  }
  if (!finished) throw new Error('The connection closed before the research finished.');
}
