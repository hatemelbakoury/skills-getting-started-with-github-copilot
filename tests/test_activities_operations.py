"""
Activity Operations Tests using AAA (Arrange-Act-Assert) Pattern

This module tests complex operations involving multiple activities and participants.
"""

import pytest


class TestActivityParticipantManagement:
    """Tests for managing participants across activities"""

    def test_same_student_can_signup_for_multiple_activities(self, client, reset_activities):
        """
        Test that one student can sign up for multiple different activities

        Arrange: Select test student and multiple activities
        Act: Sign up same student for each activity
        Assert: Verify student appears in all activities
        """
        # Arrange
        student_email = "versatile@mergington.edu"
        activities_to_join = ["Basketball", "Art Studio", "Music Band"]

        # Act
        for activity in activities_to_join:
            response = client.post(
                f"/activities/{activity}/signup",
                params={"email": student_email}
            )
            assert response.status_code == 200

        # Assert
        activities_data = client.get("/activities").json()
        for activity in activities_to_join:
            assert student_email in activities_data[activity]["participants"]

    def test_signup_and_unregister_cycle(self, client, reset_activities):
        """
        Test complete signup and unregister cycle

        Arrange: Pick activity name and student email
        Act: Sign up, then immediately unregister
        Assert: Verify student is not in activity after both operations
        """
        # Arrange
        activity_name = "Tennis"
        email = "cycling@mergington.edu"
        activities_before = client.get("/activities").json()
        initial_count = len(activities_before[activity_name]["participants"])

        # Act - Signup
        response_signup = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # Act - Unregister
        response_unregister = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )

        # Assert
        assert response_signup.status_code == 200
        assert response_unregister.status_code == 200

        activities_after = client.get("/activities").json()
        final_count = len(activities_after[activity_name]["participants"])
        assert final_count == initial_count


class TestActivityAvailability:
    """Tests for activity availability and capacity management"""

    def test_activity_availability_decreases_after_signup(self, client, reset_activities):
        """
        Test that available spots decrease when student signs up

        Arrange: Get initial available spots for an activity
        Act: Sign up a new student
        Assert: Verify available spots decreased by one
        """
        # Arrange
        activity_name = "Programming Class"
        email = "newcomer@mergington.edu"
        activities_before = client.get("/activities").json()
        max_participants = activities_before[activity_name]["max_participants"]
        initial_participants = len(activities_before[activity_name]["participants"])
        initial_availability = max_participants - initial_participants

        # Act
        client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # Assert
        activities_after = client.get("/activities").json()
        final_participants = len(activities_after[activity_name]["participants"])
        final_availability = max_participants - final_participants
        assert final_availability == initial_availability - 1

    def test_activity_capacity_consistency(self, client, reset_activities):
        """
        Test that current implementation allows unlimited signups

        Note: Current API doesn't enforce max_participants limits.
        This test verifies the current behavior.

        Arrange: Get activity with current participants
        Act: Attempt multiple consecutive signups beyond capacity
        Assert: Verify all signups are accepted (current behavior)
        """
        # Arrange
        activity_name = "Debate Club"
        activities_data = client.get("/activities").json()
        max_participants = activities_data[activity_name]["max_participants"]
        initial_count = len(activities_data[activity_name]["participants"])

        # Act: Try to add more than max capacity
        for i in range(max_participants + 5):
            email = f"overflow{i}@mergington.edu"
            response = client.post(
                f"/activities/{activity_name}/signup",
                params={"email": email}
            )
            # Current implementation accepts all
            assert response.status_code == 200

        # Assert: Verify we exceeded max capacity (current behavior)
        activities_final = client.get("/activities").json()
        actual_participants = len(activities_final[activity_name]["participants"])
        assert actual_participants > max_participants


class TestActivityData:
    """Tests for activity data consistency"""

    def test_activity_descriptions_are_consistent(self, client, reset_activities):
        """
        Test that activity descriptions remain constant

        Arrange: Fetch activities twice
        Act: Compare descriptions from both fetches
        Assert: Verify descriptions are identical
        """
        # Arrange
        activities_first_fetch = client.get("/activities").json()

        # Act: Make changes (signup/unregister)
        client.post(
            "/activities/Basketball/signup",
            params={"email": "test@mergington.edu"}
        )

        # Assert
        activities_second_fetch = client.get("/activities").json()
        for activity_name in activities_first_fetch:
            assert (activities_first_fetch[activity_name]["description"] ==
                    activities_second_fetch[activity_name]["description"])

    def test_activity_schedule_is_immutable(self, client, reset_activities):
        """
        Test that activity schedules don't change

        Arrange: Get initial activity schedules
        Act: Perform various endpoints operations
        Assert: Verify all schedules remain unchanged
        """
        # Arrange
        activities_initial = client.get("/activities").json()
        schedules_initial = {
            name: data["schedule"]
            for name, data in activities_initial.items()
        }

        # Act: Perform multiple operations
        client.post("/activities/Chess Club/signup", params={"email": "a@test.edu"})
        client.post("/activities/Tennis/signup", params={"email": "b@test.edu"})
        client.post("/activities/Tennis/signup", params={"email": "c@test.edu"})

        # Assert
        activities_final = client.get("/activities").json()
        for name, data in activities_final.items():
            assert schedules_initial[name] == data["schedule"]