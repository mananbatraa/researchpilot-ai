import sample from './demo_data.json';
import type { Result, StepName } from '../api';

export const DEMO_DISCLAIMER = 'Demo mode: this is a pre-recorded sample run, not live research on your question. Run with real API keys for live results.';

type Handlers = {
  onStep: (e: { step: StepName; status: 'running' | 'done'; output?: Partial<Result> }) => void;
  onResult: (r: Result) => void;
};

const steps: [StepName, Partial<Result>][] = [
  ['research', { sources: sample.sources }],
  ['analyze', { analysis: sample.analysis }],
  ['fact_check', { fact_check: sample.fact_check }],
  ['report', { report: sample.report }],
];

function wait(ms: number, signal?: AbortSignal) {
  return new Promise<void>((resolve, reject) => {
    const t = setTimeout(resolve, ms);
    signal?.addEventListener('abort', () => { clearTimeout(t); reject(new DOMException('Aborted', 'AbortError')); }, { once: true });
  });
}

/** Replays the canned sample in the browser with the same events the backend stream sends. No backend needed. */
export async function simulateResearch(handlers: Handlers, signal?: AbortSignal, stepMs = 1600) {
  for (const [step, output] of steps) {
    handlers.onStep({ step, status: 'running' });
    await wait(stepMs, signal);
    handlers.onStep({ step, status: 'done', output });
  }
  handlers.onResult({ ...sample, disclaimer: DEMO_DISCLAIMER, demo: true });
}
