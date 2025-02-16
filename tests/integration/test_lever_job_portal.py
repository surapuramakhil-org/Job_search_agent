import unittest
from unittest.mock import MagicMock, patch
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from ai_hawk.job_applier import AIHawkJobApplier
from job_portals.lever.application_page import LeverApplicationPage
from job_portals.base_job_portal import BaseJobPortal
from job import Job
from ai_hawk.llm.llm_manager import GPTAnswerer
from job_application_saver import ApplicationSaver
import os

from main import init_browser

class TestLeverJobPortalIntegration(unittest.TestCase):
    def setUp(self):
        self.driver = init_browser()

        # Mock dependencies
        self.mock_job_page = MagicMock()
        self.mock_application_page = MagicMock(spec=LeverApplicationPage)
        self.mock_job_portal = MagicMock(spec=BaseJobPortal)
        self.mock_job_portal.get_application_page.return_value = self.mock_application_page
        self.mock_gpt_answerer = MagicMock(spec=GPTAnswerer)
        self.mock_gpt_answerer.answer_question_from_options.side_effect = lambda question, options: options[0]
        self.mock_gpt_answerer.answer_question_textual_wide_range.side_effect = lambda question: "Sample answer"
        self.mock_gpt_answerer.answer_question_numeric.side_effect = lambda question: "12345"
        self.mock_gpt_answerer.is_job_suitable.return_value = (True, 0.9, "Suitable job")
        self.mock_resume_generator_manager = MagicMock()
        self.mock_work_preferences = {"keywords_whitelist": ["Python", "Django"]}

        # Initialize AIHawkJobApplier with mocks
        self.job_applier = AIHawkJobApplier(
            job_portal=self.mock_job_portal,
            resume_dir=None,
            set_old_answers=[],
            gpt_answerer=self.mock_gpt_answerer,
            work_preferences=self.mock_work_preferences,
            resume_generator_manager=self.mock_resume_generator_manager,
        )

    def tearDown(self):
        # Quit the WebDriver
        self.driver.quit()

    def get_job_url(self, relative_path: str) ->str:
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        file_path = os.path.join(project_root, relative_path)

        return f"file://{file_path}"

    @patch.object(ApplicationSaver, 'save')
    def test_lever_apply_to_job_success(self, mock_save):
        # Mock job object
        self.mock_job = Job(
            title="Software Engineer",
            company="Tech Company",
            description="Looking for a Python developer with Django experience.",
            link=self.get_job_url("tests/resources/lever_application_pages/Nielsen - Senior Software Engineer - Bigdata ( Java _ Scala _ Python , Spark, SQL , AWS).html")
        )

        # Add logging
        print(f"Testing Lever job {self.mock_job.link} ")

        # Mock methods to simulate successful job application
        self.mock_job_page.goto_job_page.return_value = None
        self.mock_job_page.get_job_description.return_value = self.mock_job.description
        self.mock_job_page.get_recruiter_link.return_value = "https://linkedin.com/recruiter"

        # Call the method under test
        self.job_applier.apply_to_job(self.mock_job)

        # Assertions
        self.mock_job_page.goto_job_page.assert_called_once_with(self.mock_job)
        self.mock_job_page.get_job_description.assert_called_once_with(self.mock_job)
        self.mock_job_page.get_recruiter_link.assert_called_once()
        self.mock_gpt_answerer.is_job_suitable.assert_called_once()
        self.mock_application_page.has_submit_button.assert_called_once()
        mock_save.assert_called_once()
