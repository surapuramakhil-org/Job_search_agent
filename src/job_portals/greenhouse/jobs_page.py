"""
Greenhouse Jobs Page using browser-use AI agent.

This module provides job listing functionality for Greenhouse job boards
using the browser-use AI agent for agentic automation.
"""

import asyncio
from typing import List, Optional, Any

from browser_use import Agent, Browser
from browser_use.browser.profile import BrowserProfile

from job import Job, JobState
from job_portals.base_job_portal import BaseJobsPage
from logger import logger


class GreenhouseJobsPage(BaseJobsPage):
    """
    Greenhouse job listing page using browser-use AI agent.

    Browses company job boards at boards.greenhouse.io/{company}
    to find job listings matching work preferences.
    """

    GREENHOUSE_JOB_BOARD_URL = "https://boards.greenhouse.io"

    def __init__(self, driver, work_preferences):
        """
        Initialize the Greenhouse jobs page.

        Args:
            driver: Selenium WebDriver instance (kept for compatibility).
            work_preferences: User's work preferences dictionary.
        """
        super().__init__(driver, work_preferences)
        self.jobs: List[Job] = []
        self.current_company: Optional[str] = None
        self._browser: Optional[Browser] = None
        self._llm = None  # Will be set when needed

    def set_llm(self, llm):
        """Set the LLM for the browser agent."""
        self._llm = llm

    async def _get_browser(self) -> Browser:
        """Get or create browser instance."""
        if self._browser is None:
            profile = BrowserProfile(headless=False)
            self._browser = Browser(browser_profile=profile)
        return self._browser

    def next_job_page(self, position: str, location: str, page_number: int) -> None:
        """
        Navigate to the next page of job listings.

        For Greenhouse, this searches a company's job board.
        The position parameter is used as the company slug.

        Args:
            position: For Greenhouse, this should be the company slug.
            location: Location filter (optional).
            page_number: Page number for pagination.
        """
        # For Greenhouse, we use position as the company slug
        self.current_company = position

        if self._llm is None:
            logger.warning("LLM not set for Greenhouse jobs page. Using fallback.")
            self.jobs = []
            return

        # Run async search synchronously
        try:
            self.jobs = asyncio.run(
                self._search_jobs_async(position, location, page_number)
            )
        except Exception as e:
            logger.error(f"Error searching jobs: {e}")
            self.jobs = []

    async def _search_jobs_async(
        self, company_slug: str, location: Optional[str], page_number: int
    ) -> List[Job]:
        """
        Search for jobs on a company's Greenhouse board asynchronously.

        Args:
            company_slug: Company identifier in the Greenhouse URL.
            location: Optional location filter.
            page_number: Page number for pagination.

        Returns:
            List of Job objects found.
        """
        browser = await self._get_browser()

        positions = self.work_preferences.get("positions", [])
        locations = self.work_preferences.get("locations", [])

        position_text = ", ".join(positions) if positions else "any position"
        location_text = location or (", ".join(locations) if locations else "any location")

        task = f"""
        Navigate to https://boards.greenhouse.io/{company_slug}

        This is a Greenhouse job board. Look for job listings that match:
        - Positions: {position_text}
        - Locations: {location_text}

        For each matching job:
        1. Note the job title
        2. Note the job location
        3. Get the job URL (the link to the job details page)
        4. Note the department if shown

        If there are search/filter options on the page, use them to find relevant jobs.
        If jobs are paginated, focus on page {page_number + 1}.

        Return a list of all matching jobs found with their details.
        """

        try:
            agent = Agent(
                task=task,
                llm=self._llm,
                browser=browser,
                use_vision=True,
            )

            result = await agent.run()
            return self._parse_job_listings(result, company_slug)
        except Exception as e:
            logger.error(f"Error running browser agent: {e}")
            return []

    def _parse_job_listings(self, agent_result: Any, company: str) -> List[Job]:
        """Parse agent result into Job objects."""
        jobs = []

        # The agent returns results in its history/final_result
        # Parse and create Job objects
        if hasattr(agent_result, "final_result") and agent_result.final_result:
            logger.debug(f"Agent found jobs: {agent_result.final_result}")
            # TODO: Parse the agent's text output into structured Job objects
            # For now, this is a placeholder

        return jobs

    def job_tile_to_job(self, job_tile: Any) -> Job:
        """
        Convert a job tile/result to a Job object.

        Args:
            job_tile: Job data from the listing.

        Returns:
            Job object.
        """
        if isinstance(job_tile, Job):
            return job_tile

        # Handle dict-like job data
        if isinstance(job_tile, dict):
            return Job(
                portal="Greenhouse",
                id=job_tile.get("id", ""),
                title=job_tile.get("title", ""),
                company=job_tile.get("company", self.current_company or ""),
                location=job_tile.get("location", ""),
                link=job_tile.get("link", ""),
                job_state=JobState.APPLY.value,
            )

        return Job(portal="Greenhouse")

    def get_jobs_from_page(self, scroll: bool = False) -> List[Job]:
        """
        Get jobs from the current page.

        Args:
            scroll: Whether to scroll for more jobs (not used with browser-use).

        Returns:
            List of Job objects.
        """
        return self.jobs

    async def close(self):
        """Close browser resources."""
        if self._browser:
            await self._browser.stop()
            self._browser = None
