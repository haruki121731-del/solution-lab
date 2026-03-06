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
