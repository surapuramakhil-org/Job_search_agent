"""
Unit tests for Greenhouse browser agent.
"""

import unittest
from unittest.mock import MagicMock, AsyncMock, patch
from dataclasses import dataclass

from job import Job, JobState
from job_portals.greenhouse.browser_agent import (
    GreenhouseBrowserAgent,
    GreenhouseJobSearchAgent,
    GreenhouseJobApplication,
)


class TestGreenhouseJobApplication(unittest.TestCase):
    """Test GreenhouseJobApplication dataclass."""

    def test_default_values(self):
        """Test default values for job application."""
        job = Job(
            portal="Greenhouse",
            id="123",
            title="Software Engineer",
            company="TestCo",
            link="https://boards.greenhouse.io/testco/jobs/123",
        )
        application = GreenhouseJobApplication(job=job)

        self.assertEqual(application.job, job)
        self.assertIsNone(application.resume_path)
        self.assertIsNone(application.cover_letter_path)
        self.assertEqual(application.answers, {})
        self.assertEqual(application.status, "pending")
        self.assertIsNone(application.error_message)

    def test_with_resume_path(self):
        """Test job application with resume path."""
        job = Job(portal="Greenhouse", id="123")
        application = GreenhouseJobApplication(
            job=job,
            resume_path="/path/to/resume.pdf",
        )

        self.assertEqual(application.resume_path, "/path/to/resume.pdf")


class TestGreenhouseBrowserAgent(unittest.TestCase):
    """Test GreenhouseBrowserAgent class."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_llm = MagicMock()
        self.mock_profile = MagicMock()

    def test_init(self):
        """Test agent initialization."""
        agent = GreenhouseBrowserAgent(
            llm=self.mock_llm,
            job_application_profile=self.mock_profile,
            resume_path="/path/to/resume.pdf",
            headless=True,
        )

        self.assertEqual(agent.llm, self.mock_llm)
        self.assertEqual(agent.job_application_profile, self.mock_profile)
        self.assertEqual(agent.resume_path, "/path/to/resume.pdf")
        self.assertTrue(agent.headless)
        self.assertIsNone(agent.browser)

    def test_greenhouse_job_board_url(self):
        """Test that the Greenhouse job board URL is correct."""
        agent = GreenhouseBrowserAgent(
            llm=self.mock_llm,
            job_application_profile=self.mock_profile,
        )

        self.assertEqual(
            agent.GREENHOUSE_JOB_BOARD_URL,
            "https://boards.greenhouse.io",
        )

    def test_format_profile_for_agent_no_profile(self):
        """Test profile formatting with no profile."""
        agent = GreenhouseBrowserAgent(
            llm=self.mock_llm,
            job_application_profile=None,
        )

        result = agent._format_profile_for_agent()
        self.assertEqual(result, "No profile information available.")

    def test_format_profile_for_agent_with_profile(self):
        """Test profile formatting with profile data."""
        # Create mock profile with personal information
        mock_personal = MagicMock()
        mock_personal.name = "John Doe"
        mock_personal.email = "john@example.com"
        mock_personal.phone = "555-1234"

        mock_profile = MagicMock()
        mock_profile.personal_information = mock_personal

        agent = GreenhouseBrowserAgent(
            llm=self.mock_llm,
            job_application_profile=mock_profile,
        )

        result = agent._format_profile_for_agent()
        self.assertIn("John Doe", result)
        self.assertIn("john@example.com", result)
        self.assertIn("555-1234", result)

    def test_format_profile_for_agent_with_job_application_profile(self):
        """Test profile formatting with JobApplicationProfile structure."""
        # Create mock profile matching JobApplicationProfile structure
        mock_legal = MagicMock()
        mock_legal.us_work_authorization = "US Citizen"
        mock_legal.requires_us_sponsorship = "No"
        mock_legal.legally_allowed_to_work_in_us = "Yes"

        mock_work_prefs = MagicMock()
        mock_work_prefs.remote_work = "Yes"
        mock_work_prefs.open_to_relocation = "No"

        mock_availability = MagicMock()
        mock_availability.notice_period = "2 weeks"

        mock_salary = MagicMock()
        mock_salary.salary_range_usd = "$100,000 - $150,000"

        mock_profile = MagicMock()
        mock_profile.legal_authorization = mock_legal
        mock_profile.work_preferences = mock_work_prefs
        mock_profile.availability = mock_availability
        mock_profile.salary_expectations = mock_salary
        # Ensure personal_information is not present for this test
        del mock_profile.personal_information

        agent = GreenhouseBrowserAgent(
            llm=self.mock_llm,
            job_application_profile=mock_profile,
        )

        result = agent._format_profile_for_agent()
        self.assertIn("US Citizen", result)
        self.assertIn("2 weeks", result)
        self.assertIn("$100,000 - $150,000", result)

    def test_format_answers_for_agent_empty(self):
        """Test answer formatting with no answers."""
        agent = GreenhouseBrowserAgent(
            llm=self.mock_llm,
            job_application_profile=self.mock_profile,
        )

        result = agent._format_answers_for_agent({})
        self.assertEqual(result, "No pre-defined answers provided.")

    def test_format_answers_for_agent_with_answers(self):
        """Test answer formatting with answers."""
        agent = GreenhouseBrowserAgent(
            llm=self.mock_llm,
            job_application_profile=self.mock_profile,
        )

        answers = {
            "Are you authorized to work?": "Yes",
            "Years of experience": "5",
        }

        result = agent._format_answers_for_agent(answers)
        self.assertIn("Are you authorized to work?", result)
        self.assertIn("Yes", result)
        self.assertIn("Years of experience", result)
        self.assertIn("5", result)

    def test_get_sensitive_data_no_profile(self):
        """Test sensitive data extraction with no profile."""
        agent = GreenhouseBrowserAgent(
            llm=self.mock_llm,
            job_application_profile=None,
        )

        result = agent._get_sensitive_data()
        self.assertIsNone(result)

    def test_get_sensitive_data_with_profile(self):
        """Test sensitive data extraction with profile."""
        mock_personal = MagicMock()
        mock_personal.email = "john@example.com"
        mock_personal.phone = "555-1234"

        mock_profile = MagicMock()
        mock_profile.personal_information = mock_personal

        agent = GreenhouseBrowserAgent(
            llm=self.mock_llm,
            job_application_profile=mock_profile,
        )

        result = agent._get_sensitive_data()
        self.assertIsNotNone(result)
        self.assertEqual(result["email"], "john@example.com")
        self.assertEqual(result["phone"], "555-1234")


class TestGreenhouseJobSearchAgent(unittest.TestCase):
    """Test GreenhouseJobSearchAgent class."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_llm = MagicMock()
        self.work_preferences = {
            "positions": ["Software Engineer", "Developer"],
            "locations": ["San Francisco", "Remote"],
        }

    def test_init(self):
        """Test search agent initialization."""
        agent = GreenhouseJobSearchAgent(
            llm=self.mock_llm,
            work_preferences=self.work_preferences,
            headless=True,
        )

        self.assertEqual(agent.llm, self.mock_llm)
        self.assertEqual(agent.work_preferences, self.work_preferences)
        self.assertTrue(agent.headless)
        self.assertIsNone(agent.browser)


if __name__ == "__main__":
    unittest.main()
