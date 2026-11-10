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
