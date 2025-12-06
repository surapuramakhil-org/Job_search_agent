"""
Greenhouse Job Page using browser-use AI agent.

This module provides job detail page functionality for Greenhouse
using the browser-use AI agent for agentic automation.
"""

import asyncio
import traceback
from typing import Any, Optional

from browser_use import Agent, Browser
from browser_use.browser.profile import BrowserProfile

from job import Job
from job_portals.base_job_portal import BaseJobPage
from jobContext import JobContext
from logger import logger
from utils import time_utils


class GreenhouseJobPage(BaseJobPage):
    """
    Greenhouse job detail page using browser-use AI agent.

    Handles navigation to job pages and extraction of job details
    using AI-powered browser automation.
    """

    def __init__(self, driver):
        """
        Initialize the Greenhouse job page.

        Args:
            driver: Selenium WebDriver instance (kept for compatibility).
        """
        super().__init__(driver)
        self._browser: Optional[Browser] = None
        self._llm = None

    def set_llm(self, llm):
        """Set the LLM for the browser agent."""
        self._llm = llm

    async def _get_browser(self) -> Browser:
        """Get or create browser instance."""
        if self._browser is None:
            profile = BrowserProfile(headless=False)
            self._browser = Browser(browser_profile=profile)
        return self._browser

    def goto_job_page(self, job: Job):
        """
        Navigate to the job page.

        Args:
            job: Job object with the link to navigate to.
        """
        try:
            self.driver.get(job.link)
            time_utils.medium_sleep()
            logger.debug(f"Navigated to job link: {job.link}")
        except Exception as e:
            logger.error(f"Failed to navigate to job link: {job.link}, error: {str(e)}")
            raise e

    def get_apply_button(self, job_context: JobContext):
        """Get the apply button element."""
        raise NotImplementedError("Use click_apply_button instead")

    def check_for_premium_redirect(self, job: Job, max_attempts: int = 3):
        """Check for premium redirect (not applicable for Greenhouse)."""
        pass

    def click_apply_button(self, job_context: JobContext) -> None:
        """
        Click the apply button on the job page.

        Uses browser-use agent to intelligently find and click the apply button.
        """
        if self._llm is None:
            # Fallback to Selenium-based click
            self._click_apply_button_selenium(job_context)
            return

        try:
            asyncio.run(self._click_apply_button_async(job_context))
        except Exception as e:
            logger.error(f"Error clicking apply button with agent: {e}")
            # Fallback to Selenium
            self._click_apply_button_selenium(job_context)

    def _click_apply_button_selenium(self, job_context: JobContext) -> None:
        """Fallback Selenium-based apply button click."""
        from selenium.webdriver.common.by import By

        try:
            # Try multiple selectors for the apply button
            selectors = [
                (By.ID, "apply_button"),
                (By.XPATH, "//a[contains(@class, 'btn') and contains(text(), 'Apply')]"),
                (By.XPATH, "//a[contains(text(), 'Apply for this job')]"),
                (By.XPATH, "//button[contains(text(), 'Apply')]"),
                (By.XPATH, "//a[contains(@href, '#app')]"),
            ]

            for by, selector in selectors:
                try:
                    apply_button = self.driver.find_element(by, selector)
                    if apply_button.is_displayed():
                        apply_button.click()
                        return
                except Exception:
                    continue

            raise Exception("Apply button not found")

        except Exception as e:
            logger.error(f"Failed to click apply button: {e}, {traceback.format_exc()}")
            raise Exception("Failed to click apply button")

    async def _click_apply_button_async(self, job_context: JobContext) -> None:
        """Click apply button using browser-use agent."""
        browser = await self._get_browser()

        task = """
        Find and click the "Apply" or "Apply for this job" button on this page.
        Wait for the application form to load after clicking.
        """

        agent = Agent(
            task=task,
            llm=self._llm,
            browser=browser,
            use_vision=True,
        )

        await agent.run()

    def get_location(self) -> str:
        """Get the job location."""
        from selenium.webdriver.common.by import By

        try:
            selectors = [
                (By.CLASS_NAME, "location"),
                (By.XPATH, "//div[contains(@class, 'location')]"),
            ]

            for by, selector in selectors:
                try:
                    element = self.driver.find_element(by, selector)
                    if element.is_displayed():
                        return element.text.strip()
                except Exception:
                    continue

            return ""
        except Exception as e:
            logger.error(f"Failed to get location: {e}")
            return ""

    def get_job_categories(self) -> dict:
        """Get job categories."""
        from selenium.webdriver.common.by import By

        categories = {}
        try:
            # Try to find department
            try:
                dept = self.driver.find_element(
                    By.XPATH, "//div[contains(@class, 'department')]"
                )
                if dept.is_displayed():
                    categories["department"] = dept.text.strip()
            except Exception:
                pass

            # Add location
            location = self.get_location()
            if location:
                categories["location"] = location

        except Exception as e:
            logger.error(f"Failed to get job categories: {e}")

        return categories

    def get_job_description(self, job: Job) -> str:
        """Get the job description."""
        from selenium.webdriver.common.by import By

        try:
            selectors = [
                (By.ID, "content"),
                (By.CLASS_NAME, "content"),
                (By.XPATH, "//div[@id='content']"),
                (By.XPATH, "//div[contains(@class, 'content')]"),
            ]

            for by, selector in selectors:
                try:
                    element = self.driver.find_element(by, selector)
                    if element.is_displayed():
                        return element.text
                except Exception:
                    continue

            return ""
        except Exception as e:
            logger.error(f"Error getting job description: {e}")
            return ""

    def get_recruiter_link(self) -> str:
        """Get recruiter link (not typically available on Greenhouse)."""
        return ""

    async def close(self):
        """Close browser resources."""
        if self._browser:
            await self._browser.stop()
            self._browser = None
