import json
from app import main
from app.config import Settings
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health():
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json()['status'] == 'ok'

def test_research_rejects_short_question():
    response = client.post('/api/research', json={'question': 'too short'})
    assert response.status_code == 422


def _parse_sse(text):
    events = []
    for block in text.strip().split('\n\n'):
        lines = dict(line.split(': ', 1) for line in block.splitlines())
        events.append((lines['event'], json.loads(lines['data'])))
    return events


class FakeWorkflow:
    def __init__(self, fail_on=None):
        self.fail_on = fail_on

    def stream(self, state, stream_mode):
        outputs = {
            'research': {'sources': [{'id': 'S1', 'title': 'T', 'url': 'https://example.com', 'content': 'c'}]},
            'analyze': {'analysis': 'analysis [S1]'},
            'fact_check': {'fact_check': 'SUPPORTED [S1]'},
            'report': {'report': '# Report'},
        }
        for node, output in outputs.items():
            if node == self.fail_on:
                raise RuntimeError('boom')
            yield {node: output}


def _with_keys(monkeypatch, workflow):
    monkeypatch.setattr(main.settings, 'gemini_api_key', 'x')
    monkeypatch.setattr(main.settings, 'tavily_api_key', 'x')
    monkeypatch.setattr(main, 'workflow', workflow)


def test_stream_emits_each_step_then_result(monkeypatch):
    _with_keys(monkeypatch, FakeWorkflow())
    response = client.post('/api/research/stream', json={'question': 'What is a long enough question?'})
    assert response.status_code == 200
    assert response.headers['content-type'].startswith('text/event-stream')
    events = _parse_sse(response.text)
    done = [data['step'] for name, data in events if name == 'step' and data['status'] == 'done']
    assert done == ['research', 'analyze', 'fact_check', 'report']
    name, result = events[-1]
    assert name == 'result'
    assert result['report'] == '# Report' and result['sources'][0]['id'] == 'S1'


def test_stream_reports_failing_step(monkeypatch):
    _with_keys(monkeypatch, FakeWorkflow(fail_on='fact_check'))
    events = _parse_sse(client.post('/api/research/stream', json={'question': 'What is a long enough question?'}).text)
    assert events[-1][0] == 'error'
    assert events[-1][1]['step'] == 'fact_check'


def test_stream_requires_keys(monkeypatch):
    monkeypatch.setattr(main.settings, 'gemini_api_key', '')
    response = client.post('/api/research/stream', json={'question': 'What is a long enough question?'})
    assert response.status_code == 503


def test_cors_origins_parsed_from_comma_list():
    s = Settings(cors_origins='https://a.vercel.app/, http://localhost:5173 ,')
    assert s.cors_origin_list == ['https://a.vercel.app', 'http://localhost:5173']


def test_cors_allows_configured_origin():
    response = client.options('/api/research/stream', headers={'Origin': 'http://localhost:5173', 'Access-Control-Request-Method': 'POST'})
    assert response.headers.get('access-control-allow-origin') == 'http://localhost:5173'


def test_demo_mode_streams_sample_without_keys(monkeypatch):
    from app.demo import DemoWorkflow, SAMPLE
    monkeypatch.setattr(main.settings, 'demo_mode', True)
    monkeypatch.setattr(main.settings, 'gemini_api_key', '')
    monkeypatch.setattr(main.settings, 'tavily_api_key', '')
    monkeypatch.setattr(main, 'workflow', DemoWorkflow(step_delay=0))
    events = _parse_sse(client.post('/api/research/stream', json={'question': 'Anything at all, long enough?'}).text)
    done = [data['step'] for name, data in events if name == 'step' and data['status'] == 'done']
    assert done == ['research', 'analyze', 'fact_check', 'report']
    name, result = events[-1]
    assert name == 'result' and result['demo'] is True
    assert result['report'] == SAMPLE['report']
    assert client.post('/api/research', json={'question': 'Anything at all, long enough?'}).json()['demo'] is True


def test_demo_sources_are_all_cited_and_frontend_copy_matches():
    from pathlib import Path
    from app.demo import SAMPLE
    for source in SAMPLE['sources']:
        assert f"[{source['id']}]" in SAMPLE['report']
        assert source['url'] in SAMPLE['report']
    frontend_copy = Path(__file__).parents[2] / 'frontend' / 'src' / 'demo' / 'demo_data.json'
    assert json.loads(frontend_copy.read_text()) == SAMPLE
