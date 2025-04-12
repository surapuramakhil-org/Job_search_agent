import json
import unittest
from unittest.mock import MagicMock, patch
from selenium import webdriver

from selenium.webdriver.common.by import By
from parameterized import parameterized
from job_applier import AIHawkJobApplier
from job_portals.lever.application_page import LeverApplicationPage
from job_portals.base_job_portal import BaseJobPortal
from job import Job

from job_application_saver import ApplicationSaver
from job_portals.lever.job_page import LeverJobPage
from llm.ai_answerer import AiAnswerer
from main import init_browser
from utils import browser_utils


class TestLeverJobPortalIntegration(unittest.TestCase):

    def setUp(self):
        # Initialize browser once per test
        self.driver = init_browser()
        browser_utils.set_default_driver(self.driver)

        # Configure base mocks
        self._setup_application_mocks()
        self._setup_gpt_mocks()

        # Initialize core test component
        self.job_applier = AIHawkJobApplier(
            job_portal=self.mock_job_portal,
            resume_dir=None,
            set_old_answers=[],
            gpt_answerer=self.mock_gpt_answerer,
            work_preferences={"keywords_whitelist": []},
            resume_generator_manager=MagicMock(),
        )
        
        # Mock the _save_answer_to_json method to prevent modifying cache during tests
        self.job_applier._save_answer_to_json = MagicMock()

    def _setup_application_mocks(self):
        """Configure application page and job portal mocks"""
        self.mock_job_page = LeverJobPage(self.driver)
        self.mock_application_page = LeverApplicationPage(self.driver)

        self.mock_job_portal = MagicMock(spec=BaseJobPortal)
        self.mock_job_portal.application_page = self.mock_application_page
        self.mock_job_portal.job_page = self.mock_job_page
        self.mock_application_page._handle_location_input = MagicMock()

    def _setup_gpt_mocks(self):
        """Configure standard GPT response behavior"""
        self.mock_gpt_answerer = MagicMock(spec=AiAnswerer)
        self.mock_gpt_answerer.answer_question_from_options.side_effect = (
            lambda q, o: o[0]
        )
        self.mock_gpt_answerer.answer_question_textual_wide_range.side_effect = (
            lambda q: "Sample answer"
        )
        self.mock_gpt_answerer.answer_question_numeric.side_effect = lambda q: "12345"
        self.mock_gpt_answerer.is_job_suitable.return_value = (
            True,
            0.9,
            "Suitable job",
        )

    def tearDown(self):
        self.driver.quit()

    @parameterized.expand([
        (
            "job1",
            "https://jobs.lever.co/foodstuffs/b9077163-d168-4379-9a5e-d3953d8855e8",
            "tests/resources/lever_application_pages/job1/Foodstuffs North Island - Commercial Analyst - Wholesale_job_page.html",
            "tests/resources/lever_application_pages/job1/Foodstuffs North Island - Commercial Analyst - Wholesale_application_page.html",
            "tests/resources/lever_application_pages/job1/Foodstuffs North Island - Commercial Analyst - Wholesale_confirmation_page.html",
        ),
        (
            "job2",
            "https://jobs.lever.co/agiloft/5b181cdd-fa45-40e6-b561-ec268e292914",
            "tests/resources/lever_application_pages/job2/Agiloft - Senior Software Engineer, Full Stack_job_page.html",
            "tests/resources/lever_application_pages/job2/Agiloft - Senior Software Engineer, Full Stack_application_page.html",
            "tests/resources/lever_application_pages/job2/Agiloft - Senior Software Engineer, Full Stack_confirmation_page.html",
        )
    ])
    @patch.object(ApplicationSaver, "save")
    def test_apply_flow(self, name, lever_url , job_page, application_page, confirmation_page, mock_save):
        
        print(f"Testing job application flow: {name}, URL: {lever_url}")

        job = Job(
            title="Test Job",
            company="Test company",
            description="Test description",
            link=self._local_url(job_page),
        )

        self.mock_job_page.click_apply_button = MagicMock(
            side_effect=lambda _: self.driver.get(
                self._local_url(application_page)
            )
        )

        self.mock_application_page.click_submit_button = MagicMock(
            side_effect=lambda: self.driver.get(
            self._local_url(confirmation_page)
            )
        )

        self.job_applier.apply_to_job(job)
        mock_save.assert_called_once()
        self.mock_gpt_answerer.is_job_suitable.assert_called_once()

    def _local_url(self, path):
        from pathlib import Path

        return Path(path).resolve().as_uri()
