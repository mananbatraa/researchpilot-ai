"""Keyless demo mode: replays a canned, source-cited run with realistic pacing.

Enabled with DEMO_MODE=1. No Gemini or Tavily calls are made, so no API keys are needed.
The sample answers the default question in the UI whatever question is asked.
"""
from __future__ import annotations
import json
import time
from pathlib import Path
from typing import Any, Iterator

SAMPLE: dict[str, Any] = json.loads((Path(__file__).parent / "demo_data.json").read_text())
DEMO_DISCLAIMER = "Demo mode: this is a pre-recorded sample run, not live research on your question. Run with real API keys for live results."

_OUTPUTS = [
    ("research", {"sources": SAMPLE["sources"]}),
    ("analyze", {"analysis": SAMPLE["analysis"]}),
    ("fact_check", {"fact_check": SAMPLE["fact_check"]}),
    ("report", {"report": SAMPLE["report"]}),
]


class DemoWorkflow:
    def __init__(self, step_delay: float = 1.6):
        self.step_delay = step_delay

    def stream(self, state: dict[str, Any], stream_mode: str = "updates") -> Iterator[dict[str, Any]]:
        for node, output in _OUTPUTS:
            time.sleep(self.step_delay)
            yield {node: output}

    def invoke(self, state: dict[str, Any]) -> dict[str, Any]:
        result = dict(state)
        for update in self.stream(state):
            for output in update.values():
                result.update(output)
        return result
