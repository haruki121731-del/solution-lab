from fastapi.testclient import TestClient

from app import app


def test_health_endpoint() -> None:
    with TestClient(app) as client:
        response = client.get('/health')
        assert response.status_code == 200
        assert response.json()['status'] == 'healthy'


def test_solve_endpoint() -> None:
    with TestClient(app) as client:
        response = client.post(
            '/solve',
            json={
                'problem_description': 'The signup flow is dropping users at the verification stage.',
                'max_cycles': 5,
                'allow_external_research': True,
                'context': {'team_size': 3},
            },
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload['top_candidate'] is not None
        assert payload['cycles_completed'] >= 4


def test_solve_and_retrieve() -> None:
    with TestClient(app) as client:
        # Create session
        response = client.post(
            '/solve',
            json={
                'problem_description': 'Our API latency is too high during peak traffic.',
                'max_cycles': 5,
                'allow_external_research': False,
            },
        )
        assert response.status_code == 200
        created = response.json()
        session_id = created['session_id']

        # List sessions
        list_resp = client.get('/sessions')
        assert list_resp.status_code == 200
        sessions = list_resp.json()
        assert any(s['session_id'] == session_id for s in sessions)

        # Get specific session
        get_resp = client.get(f'/sessions/{session_id}')
        assert get_resp.status_code == 200
        retrieved = get_resp.json()
        assert retrieved['session_id'] == session_id
        assert retrieved['problem']['root_problem'] == created['problem']['root_problem']


def test_session_not_found() -> None:
    with TestClient(app) as client:
        response = client.get('/sessions/nonexistent-id')
        assert response.status_code == 404


def test_root_endpoint() -> None:
    with TestClient(app) as client:
        response = client.get('/')
        assert response.status_code == 200
        data = response.json()
        assert 'name' in data
        assert 'version' in data
        assert 'endpoints' in data
