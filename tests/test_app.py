"""
Tests for the Mergington High School API
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add src directory to path so we can import app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture
def reset_activities():
    """Reset activities to a known state before each test"""
    # Store original state
    from app import activities
    original_state = {}
    for activity_name, activity_data in activities.items():
        original_state[activity_name] = {
            "description": activity_data["description"],
            "schedule": activity_data["schedule"],
            "max_participants": activity_data["max_participants"],
            "participants": activity_data["participants"].copy()
        }
    
    yield
    
    # Restore original state
    for activity_name in activities:
        activities[activity_name]["participants"] = original_state[activity_name]["participants"].copy()


class TestGetActivities:
    """Tests for GET /activities endpoint"""
    
    def test_get_activities_returns_200(self, client):
        """Test that getting activities returns a 200 status code"""
        response = client.get("/activities")
        assert response.status_code == 200
    
    def test_get_activities_returns_dict(self, client):
        """Test that activities endpoint returns a dictionary"""
        response = client.get("/activities")
        data = response.json()
        assert isinstance(data, dict)
    
    def test_get_activities_contains_chess_club(self, client):
        """Test that Chess Club is in the activities"""
        response = client.get("/activities")
        data = response.json()
        assert "Chess Club" in data
    
    def test_activity_has_required_fields(self, client):
        """Test that each activity has required fields"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_data in data.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_returns_200(self, client, reset_activities):
        """Test that signup returns a 200 status code"""
        response = client.post(
            "/activities/Chess Club/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
    
    def test_signup_adds_participant(self, client, reset_activities):
        """Test that signup adds a participant to the activity"""
        response = client.post(
            "/activities/Chess Club/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        
        # Verify participant was added
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert "newstudent@mergington.edu" in activities_data["Chess Club"]["participants"]
    
    def test_signup_returns_message(self, client, reset_activities):
        """Test that signup returns a success message"""
        response = client.post(
            "/activities/Chess Club/signup?email=newstudent@mergington.edu"
        )
        data = response.json()
        assert "message" in data
        assert "newstudent@mergington.edu" in data["message"]
    
    def test_signup_duplicate_returns_400(self, client, reset_activities):
        """Test that signing up twice returns 400 error"""
        email = "michael@mergington.edu"  # Already signed up for Chess Club
        response = client.post(
            f"/activities/Chess Club/signup?email={email}"
        )
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]
    
    def test_signup_invalid_activity_returns_404(self, client):
        """Test that signing up for non-existent activity returns 404"""
        response = client.post(
            "/activities/Fake Activity/signup?email=student@mergington.edu"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]
    
    def test_signup_multiple_activities(self, client, reset_activities):
        """Test that a student can sign up for multiple activities"""
        email = "newstudent@mergington.edu"
        
        response1 = client.post(
            f"/activities/Chess Club/signup?email={email}"
        )
        response2 = client.post(
            f"/activities/Programming Class/signup?email={email}"
        )
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # Verify student is in both activities
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert email in activities_data["Chess Club"]["participants"]
        assert email in activities_data["Programming Class"]["participants"]


class TestUnregisterFromActivity:
    """Tests for POST /activities/{activity_name}/unregister endpoint"""
    
    def test_unregister_returns_200(self, client, reset_activities):
        """Test that unregister returns a 200 status code"""
        email = "michael@mergington.edu"  # Already signed up for Chess Club
        response = client.post(
            f"/activities/Chess Club/unregister?email={email}"
        )
        assert response.status_code == 200
    
    def test_unregister_removes_participant(self, client, reset_activities):
        """Test that unregister removes a participant from the activity"""
        email = "michael@mergington.edu"
        response = client.post(
            f"/activities/Chess Club/unregister?email={email}"
        )
        assert response.status_code == 200
        
        # Verify participant was removed
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert email not in activities_data["Chess Club"]["participants"]
    
    def test_unregister_returns_message(self, client, reset_activities):
        """Test that unregister returns a success message"""
        email = "michael@mergington.edu"
        response = client.post(
            f"/activities/Chess Club/unregister?email={email}"
        )
        data = response.json()
        assert "message" in data
        assert email in data["message"]
    
    def test_unregister_not_signed_up_returns_400(self, client, reset_activities):
        """Test that unregistering a student not signed up returns 400"""
        response = client.post(
            "/activities/Chess Club/unregister?email=notregistered@mergington.edu"
        )
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"]
    
    def test_unregister_invalid_activity_returns_404(self, client):
        """Test that unregistering from non-existent activity returns 404"""
        response = client.post(
            "/activities/Fake Activity/unregister?email=student@mergington.edu"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]


class TestRootRedirect:
    """Tests for GET / endpoint"""
    
    def test_root_redirects(self, client):
        """Test that root endpoint redirects to static index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"
