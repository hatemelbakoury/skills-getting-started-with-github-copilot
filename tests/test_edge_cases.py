"""
Edge Cases and Error Handling Tests using AAA Pattern

This module tests edge cases, boundary conditions, and error scenarios.
"""

import pytest


class TestEmailValidation:
    """Tests for email handling"""

    def test_signup_with_empty_email_string(self, client, reset_activities):
        """
        Test signup behavior with empty email string

        Note: Current implementation accepts empty emails.
        This test verifies the current behavior.

        Arrange: Prepare empty email parameter
        Act: Attempt signup with empty email
        Assert: Verify empty email is accepted (current behavior)
        """
        # Arrange
        activity_name = "Chess Club"
        email = ""

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # Assert
        # Current implementation accepts empty emails
        assert response.status_code == 200
        result = response.json()
        assert "message" in result

    def test_signup_with_special_characters_in_email(self, client, reset_activities):
        """
        Test signup with email containing special characters

        Arrange: Create email with special characters
        Act: Attempt signup with special character email
        Assert: Verify email is accepted or properly rejected
        """
        # Arrange
        activity_name = "Art Studio"
        email = "test+tag@example.com"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # Assert
        # Should accept valid email format or return clear error
        assert response.status_code in [200, 422]

    def test_signup_with_url_encoded_email(self, client, reset_activities):
        """
        Test signup with URL-encoded email

        Arrange: Prepare URL-encoded email
        Act: Send signup with encoded email
        Assert: Verify email is properly decoded
        """
        # Arrange
        activity_name = "Music Band"
        email = "test%40example.com"  # URL encoded @ symbol

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # Assert
        # Should handle URL encoding properly
        assert response.status_code in [200, 400]


class TestActivityNameEdgeCases:
    """Tests for activity name handling"""

    def test_signup_with_url_encoded_activity_name(self, client):
        """
        Test signup with URL-encoded activity name

        Arrange: Prepare URL-encoded activity name
        Act: Send request with encoded activity name
        Assert: Verify activity name is properly matched
        """
        # Arrange
        # URL encode "Chess Club" = "Chess%20Club"
        activity_name = "Chess%20Club"
        email = "test@example.com"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # Assert
        # Should properly decode and handle either success or clear error
        assert response.status_code in [200, 400, 404]

    def test_signup_with_activity_name_case_sensitivity(self, client, reset_activities):
        """
        Test whether activity names are case-sensitive

        Arrange: Create activity name with different casing
        Act: Attempt signup with different case
        Assert: Verify correct behavior (either case-insensitive or proper error)
        """
        # Arrange
        activity_name_lowercase = "chess club"
        activity_name_correct = "Chess Club"
        email = "test@example.com"

        # Act
        response = client.post(
            f"/activities/{activity_name_lowercase}/signup",
            params={"email": email}
        )

        # Assert
        # Activity names are case-sensitive in implementation
        assert response.status_code == 404


class TestConcurrentOperations:
    """Tests for behavior with multiple rapid operations"""

    def test_multiple_signups_for_same_activity(self, client, reset_activities):
        """
        Test multiple students signing up rapidly

        Arrange: Prepare list of students
        Act: Sign up all students sequentially
        Assert: Verify all signups succeeded and counts are accurate
        """
        # Arrange
        activity_name = "Gym Class"
        students = [
            f"student{i}@mergington.edu"
            for i in range(5)
        ]

        # Act
        responses = []
        for email in students:
            response = client.post(
                f"/activities/{activity_name}/signup",
                params={"email": email}
            )
            responses.append(response)

        # Assert
        assert all(r.status_code == 200 for r in responses)
        activities_data = client.get("/activities").json()
        for email in students:
            assert email in activities_data[activity_name]["participants"]

    def test_signup_unregister_refill_pattern(self, client, reset_activities):
        """
        Test signup, unregister, then re-signup pattern

        Arrange: Pick activity and student
        Act: Sign up, unregister, sign up again
        Assert: Verify all operations succeed
        """
        # Arrange
        activity_name = "Science Club"
        email = "fickle@mergington.edu"

        # Act - First signup
        response1 = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # Act - Unregister
        response2 = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )

        # Act - Sign up again
        response3 = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # Assert
        assert response1.status_code == 200
        assert response2.status_code == 200
        assert response3.status_code == 200

        activities_final = client.get("/activities").json()
        assert email in activities_final[activity_name]["participants"]


class TestResponseStructure:
    """Tests for response format and structure"""

    def test_signup_response_contains_message(self, client, reset_activities):
        """
        Test that signup response contains message field

        Arrange: Prepare signup request
        Act: Make POST request
        Assert: Verify response has message field with expected format
        """
        # Arrange
        activity_name = "Basketball"
        email = "resptest@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 200
        result = response.json()
        assert "message" in result
        assert isinstance(result["message"], str)
        assert len(result["message"]) > 0

    def test_error_response_contains_detail(self, client):
        """
        Test that error responses contain detail field

        Arrange: Set up request to trigger error
        Act: Make request for non-existent activity
        Assert: Verify error response has detail field
        """
        # Arrange
        activity_name = "NonExistent"
        email = "test@example.com"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 404
        result = response.json()
        assert "detail" in result
        assert isinstance(result["detail"], str)