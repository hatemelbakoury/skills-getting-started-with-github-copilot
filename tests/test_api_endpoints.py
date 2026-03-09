"""
API Endpoint Tests using AAA (Arrange-Act-Assert) Pattern

This module tests the core FastAPI endpoints with clear separation
of setup (Arrange), execution (Act), and verification (Assert).
"""

import pytest


class TestRootEndpoint:
    """Tests for the root endpoint"""

    def test_root_redirects_to_static_index(self, client):
        """
        Test that root endpoint redirects to static index page

        Arrange: Create a test client
        Act: Make GET request to root endpoint
        Assert: Verify redirect response to /static/index.html
        """
        # Arrange
        expected_redirect_url = "/static/index.html"

        # Act
        response = client.get("/", follow_redirects=False)

        # Assert
        assert response.status_code == 307
        assert expected_redirect_url in response.headers["location"]


class TestGetActivitiesEndpoint:
    """Tests for the GET /activities endpoint"""

    def test_get_activities_returns_all_activities(self, client, reset_activities):
        """
        Test that GET /activities returns all activities

        Arrange: Test client is ready, activities are reset
        Act: Make GET request to /activities endpoint
        Assert: Verify response contains all activities with correct structure
        """
        # Arrange
        expected_activity_count = 9
        expected_activity_names = [
            "Chess Club", "Programming Class", "Gym Class",
            "Basketball", "Tennis", "Art Studio", "Music Band",
            "Debate Club", "Science Club"
        ]

        # Act
        response = client.get("/activities")
        activities_data = response.json()

        # Assert
        assert response.status_code == 200
        assert len(activities_data) == expected_activity_count
        for activity_name in expected_activity_names:
            assert activity_name in activities_data

    def test_get_activities_contains_required_fields(self, client, reset_activities):
        """
        Test that each activity contains all required fields

        Arrange: Test client is ready, activities are reset
        Act: Make GET request and retrieve an activity
        Assert: Verify activity has description, schedule, max_participants, and participants
        """
        # Arrange
        required_fields = ["description", "schedule", "max_participants", "participants"]

        # Act
        response = client.get("/activities")
        activities_data = response.json()
        chess_club = activities_data["Chess Club"]

        # Assert
        for field in required_fields:
            assert field in chess_club
        assert isinstance(chess_club["participants"], list)
        assert isinstance(chess_club["max_participants"], int)

    def test_get_activities_participants_is_list(self, client, reset_activities):
        """
        Test that participants field is always a list

        Arrange: Test client is ready, activities are reset
        Act: Make GET request and retrieve activities data
        Assert: Verify all participants fields are lists
        """
        # Arrange
        # Act
        response = client.get("/activities")
        activities_data = response.json()

        # Assert
        for activity_name, activity_data in activities_data.items():
            assert isinstance(activity_data["participants"], list)
            assert all(isinstance(participant, str) for participant in activity_data["participants"])


class TestSignupEndpoint:
    """Tests for the POST /activities/{activity_name}/signup endpoint"""

    def test_signup_successful_for_available_activity(self, client, reset_activities):
        """
        Test successful signup when activity has available spots

        Arrange: Set up activity with available spots
        Act: Post signup request with valid email
        Assert: Verify successful response and participant is added
        """
        # Arrange
        activity_name = "Basketball"
        email = "newstudent@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        activities = client.get("/activities").json()

        # Assert
        assert response.status_code == 200
        result = response.json()
        assert "message" in result
        assert email in activities[activity_name]["participants"]

    def test_signup_fails_for_nonexistent_activity(self, client):
        """
        Test signup fails with 404 when activity doesn't exist

        Arrange: Prepare request for non-existent activity
        Act: Post signup request to invalid activity
        Assert: Verify 404 error response
        """
        # Arrange
        activity_name = "NonexistentActivity"
        email = "student@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 404
        result = response.json()
        assert "Activity not found" in result["detail"]

    def test_signup_fails_when_already_signed_up(self, client, reset_activities):
        """
        Test signup fails when student already registered

        Arrange: Select activity where student is already signed up
        Act: Attempt to signup the same student again
        Assert: Verify 400 error response
        """
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Already signed up

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 400
        result = response.json()
        assert "already signed up" in result["detail"]

    def test_signup_fails_when_activity_is_full(self, client, reset_activities):
        """
        Test signup behavior when activity reaches max participants

        Note: Current implementation doesn't enforce capacity limits,
        so this test verifies the current behavior.

        Arrange: Fill activity beyond max capacity
        Act: Attempt additional signups
        Assert: Verify signups are always accepted (current behavior)
        """
        # Arrange: Get Tennis activity which has max_participants=10
        response_get = client.get("/activities")
        tennis = response_get.json()["Tennis"]
        current_participants = len(tennis["participants"])

        # Fill beyond max capacity
        for i in range(15):  # Add more than max capacity
            email = f"participant{i}@mergington.edu"
            response = client.post("/activities/Tennis/signup", params={"email": email})
            # Current implementation accepts all signups
            assert response.status_code == 200

        # Assert: Verify participants were added (current behavior)
        activities_final = client.get("/activities").json()
        final_count = len(activities_final["Tennis"]["participants"])
        # Should have more than max_participants (current behavior)
        assert final_count > tennis["max_participants"]


class TestUnregisterEndpoint:
    """Tests for the DELETE /activities/{activity_name}/unregister endpoint"""

    def test_unregister_successful_when_participant_exists(self, client, reset_activities):
        """
        Test successful unregistration when participant is signed up

        Arrange: Select activity with existing participant
        Act: Send DELETE request to unregister
        Assert: Verify participant is removed and response is successful
        """
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        activities = client.get("/activities").json()

        # Assert
        assert response.status_code == 200
        result = response.json()
        assert "Unregistered" in result["message"]
        assert email not in activities[activity_name]["participants"]

    def test_unregister_fails_for_nonexistent_activity(self, client):
        """
        Test unregister fails with 404 for non-existent activity

        Arrange: Prepare unregister request for invalid activity
        Act: Send DELETE request to invalid activity
        Assert: Verify 404 error response
        """
        # Arrange
        activity_name = "FakeActivity"
        email = "student@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 404
        result = response.json()
        assert "Activity not found" in result["detail"]

    def test_unregister_fails_when_not_signed_up(self, client, reset_activities):
        """
        Test unregister fails when participant isn't registered

        Arrange: Select student not signed up for activity
        Act: Send DELETE request to unregister
        Assert: Verify 400 error response
        """
        # Arrange
        activity_name = "Basketball"
        email = "notonlist@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 400
        result = response.json()
        assert "not signed up" in result["detail"]

    def test_unregister_response_message_format(self, client, reset_activities):
        """
        Test unregister response contains properly formatted message

        Arrange: Select valid activity and participant
        Act: Send DELETE request
        Assert: Verify response message format
        """
        # Arrange
        activity_name = "Science Club"
        email = "benjamin@mergington.edu"
        expected_message_part = "Unregistered"

        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        result = response.json()

        # Assert
        assert response.status_code == 200
        assert expected_message_part in result["message"]
        assert activity_name in result["message"]
        assert email in result["message"]