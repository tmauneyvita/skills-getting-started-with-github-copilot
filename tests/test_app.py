from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def restore_activities():
    original_activities = deepcopy(activities)
    yield
    activities.clear()
    activities.update(original_activities)


def test_root_redirects_to_static_homepage(client):
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"

    homepage = client.get(response.headers["location"])

    assert homepage.status_code == 200
    assert "Mergington High School" in homepage.text


def test_get_activities_returns_activity_data(client):
    response = client.get("/activities")

    assert response.status_code == 200
    assert response.json() == activities


def test_signup_adds_participant(client):
    activity_name = "Art Club"
    email = "student@example.com"

    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {activity_name}"}
    assert email in activities[activity_name]["participants"]


def test_duplicate_signup_returns_conflict_without_adding_participant(client):
    activity_name = "Chess Club"
    email = "michael@mergington.edu"
    original_participants = activities[activity_name]["participants"].copy()

    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    assert response.status_code == 409
    assert activities[activity_name]["participants"] == original_participants


def test_signup_for_unknown_activity_returns_not_found(client):
    response = client.post(
        "/activities/Unknown%20Activity/signup",
        params={"email": "student@example.com"},
    )

    assert response.status_code == 404


def test_unregister_removes_participant(client):
    activity_name = "Chess Club"
    email = "michael@mergington.edu"

    response = client.delete(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {email} from {activity_name}"}
    assert email not in activities[activity_name]["participants"]


def test_unregister_unregistered_student_returns_not_found(client):
    response = client.delete(
        "/activities/Art%20Club/signup",
        params={"email": "student@example.com"},
    )

    assert response.status_code == 404


def test_unregister_from_unknown_activity_returns_not_found(client):
    response = client.delete(
        "/activities/Unknown%20Activity/signup",
        params={"email": "student@example.com"},
    )

    assert response.status_code == 404