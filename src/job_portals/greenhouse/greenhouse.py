"""
Greenhouse Job Portal implementation.

This module provides a BaseJobPortal implementation for Greenhouse
that uses the browser-use AI agent for agentic automation.
"""

from typing import List, Optional

from job import Job, JobState
from job_portals.base_job_portal import (
    BaseJobPortal,
    BaseJobsPage,
    BaseJobPage,
    BaseApplicationPage,
)
from job_portals.greenhouse.authenticator import GreenhouseAuthenticator
from job_portals.greenhouse.jobs_page import GreenhouseJobsPage
from job_portals.greenhouse.job_page import GreenhouseJobPage
from job_portals.greenhouse.application_page import GreenhouseApplicationPage
from logger import logger


class Greenhouse(BaseJobPortal):
    """
    Greenhouse job portal implementation using browser-use AI agent.

    This class provides integration with the existing AIHawkJobApplier
    by implementing the BaseJobPortal interface.
    """

    def __init__(self, driver, work_preferences):
        """
        Initialize the Greenhouse portal.

        Args:
            driver: Selenium WebDriver instance (for compatibility).
            work_preferences: User's work preferences dictionary.
        """
        self.driver = driver
        self._work_preferences = work_preferences
        self._authenticator = GreenhouseAuthenticator(driver)
        self._jobs_page = GreenhouseJobsPage(driver, work_preferences)
        self._job_page = GreenhouseJobPage(driver)
        self._application_page = GreenhouseApplicationPage(driver)

    @property
    def jobs_page(self) -> BaseJobsPage:
        return self._jobs_page

    @property
    def job_page(self) -> BaseJobPage:
        return self._job_page

    @property
    def authenticator(self):
        return self._authenticator

    @property
    def application_page(self) -> BaseApplicationPage:
        return self._application_page
