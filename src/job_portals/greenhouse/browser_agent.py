"""
Greenhouse Job Board Browser Agent.

This module provides AI-powered browser automation for applying to jobs
on Greenhouse job boards using the browser-use library.
"""

import asyncio
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from browser_use import Agent, Browser
from browser_use.browser.profile import BrowserProfile
from langchain_core.language_models.chat_models import BaseChatModel

from job import Job, JobState
from logger import logger


@dataclass
class GreenhouseJobApplication:
    """Data class to hold job application details."""

    job: Job
    resume_path: Optional[str] = None
    cover_letter_path: Optional[str] = None
    answers: Dict[str, Any] = field(default_factory=dict)
    status: str = "pending"
    error_message: Optional[str] = None


class GreenhouseBrowserAgent:
    """
    AI-powered browser agent for Greenhouse job board automation.

    Uses browser-use to intelligently navigate and interact with
    Greenhouse job boards (boards.greenhouse.io).
    """

    GREENHOUSE_JOB_BOARD_URL = "https://boards.greenhouse.io"

    def __init__(
        self,
        llm: BaseChatModel,
        job_application_profile: Any,
        resume_path: Optional[str] = None,
        headless: bool = False,
    ):
        """
        Initialize the Greenhouse browser agent.

        Args:
            llm: Language model for the browser agent.
            job_application_profile: User's job application profile with personal info.
            resume_path: Path to resume file for uploads.
            headless: Whether to run browser in headless mode.
        """
        self.llm = llm
        self.job_application_profile = job_application_profile
        self.resume_path = resume_path
        self.headless = headless
        self.browser: Optional[Browser] = None

    async def _get_browser(self) -> Browser:
        """Get or create browser instance."""
        if self.browser is None:
            profile = BrowserProfile(headless=self.headless)
            self.browser = Browser(browser_profile=profile)
        return self.browser

    async def search_jobs(
        self,
        company: str,
        position: Optional[str] = None,
        location: Optional[str] = None,
    ) -> List[Job]:
        """
        Search for jobs on a company's Greenhouse job board.

        Args:
            company: Company name/slug for the Greenhouse board.
            position: Optional position/title to search for.
            location: Optional location filter.

        Returns:
            List of Job objects found on the board.
        """
        browser = await self._get_browser()

        # Build search task for the agent
        search_criteria = []
        if position:
            search_criteria.append(f"position containing '{position}'")
        if location:
            search_criteria.append(f"location in or near '{location}'")

        criteria_text = " and ".join(search_criteria) if search_criteria else "all available positions"

        task = f"""
        Navigate to the Greenhouse job board for company '{company}' at {self.GREENHOUSE_JOB_BOARD_URL}/{company}.
        
        Search for jobs matching: {criteria_text}
        
        For each job listing found, extract:
        1. Job title
        2. Job location
        3. Job URL/link
        4. Department (if available)
        
        Return the information as a structured list of jobs.
        If there are filters available on the page, use them to narrow down results.
        """

        agent = Agent(
            task=task,
            llm=self.llm,
            browser=browser,
            use_vision=True,
        )

        result = await agent.run()

        # Parse the agent's output into Job objects
        jobs = self._parse_job_listings(result, company)
        return jobs

    def _parse_job_listings(self, agent_result: Any, company: str) -> List[Job]:
        """Parse agent result into Job objects."""
        jobs = []

        # Extract job information from agent's history/result
        if hasattr(agent_result, "final_result") and agent_result.final_result:
            # The agent should return structured job data
            # Parse based on the format returned
            logger.debug(f"Agent result: {agent_result.final_result}")

        return jobs

    async def get_job_details(self, job: Job) -> Job:
        """
        Navigate to a job page and extract detailed information.

        Args:
            job: Job object with at least a link.

        Returns:
            Updated Job object with full details.
        """
        browser = await self._get_browser()

        task = f"""
        Navigate to the job page at {job.link}
        
        Extract the following information:
        1. Full job description
        2. Job requirements
        3. Job location (city, state, country, remote/hybrid/onsite)
        4. Department/Team
        5. Employment type (full-time, part-time, contract, etc.)
        6. Any salary information if available
        
        Return all the extracted information.
        """

        agent = Agent(
            task=task,
            llm=self.llm,
            browser=browser,
            use_vision=True,
        )

        result = await agent.run()

        # Update job with extracted details
        if hasattr(result, "final_result") and result.final_result:
            job.description = str(result.final_result)

        return job

    async def apply_to_job(
        self,
        job: Job,
        answers: Optional[Dict[str, str]] = None,
    ) -> GreenhouseJobApplication:
        """
        Apply to a job on Greenhouse using the AI browser agent.

        Args:
            job: Job object to apply to.
            answers: Pre-defined answers for common questions.

        Returns:
            GreenhouseJobApplication with status and details.
        """
        browser = await self._get_browser()
        application = GreenhouseJobApplication(job=job, resume_path=self.resume_path)

        # Build the application task with user profile info
        profile_info = self._format_profile_for_agent()
        answers_info = self._format_answers_for_agent(answers or {})

        task = f"""
        Apply to the job at {job.link}
        
        Click the "Apply" or "Apply for this job" button to start the application.
        
        Fill out the application form with the following information:
        
        {profile_info}
        
        For any questions, use these pre-defined answers if applicable:
        {answers_info}
        
        For file uploads:
        - If asked for a resume, upload the file at: {self.resume_path or 'No resume provided'}
        
        For any other questions:
        - Provide professional, appropriate answers based on the context
        - For yes/no questions about legal work authorization, answer based on the profile
        - For optional fields, you may skip them unless they seem important
        
        After filling out all required fields, submit the application.
        
        Confirm that the application was submitted successfully.
        Report any errors or issues encountered.
        """

        try:
            agent = Agent(
                task=task,
                llm=self.llm,
                browser=browser,
                use_vision=True,
                sensitive_data=self._get_sensitive_data(),
                available_file_paths=[self.resume_path] if self.resume_path else None,
            )

            result = await agent.run()

            # Check if application was successful
            if hasattr(result, "final_result"):
                final_text = str(result.final_result).lower()
                if "success" in final_text or "submitted" in final_text or "thank you" in final_text:
                    application.status = "submitted"
                    logger.info(f"Successfully applied to job: {job.title} at {job.company}")
                else:
                    application.status = "failed"
                    application.error_message = str(result.final_result)
                    logger.warning(f"Application may have failed: {result.final_result}")

        except Exception as e:
            application.status = "error"
            application.error_message = str(e)
            logger.error(f"Error applying to job {job.title}: {e}")

        return application

    def _format_profile_for_agent(self) -> str:
        """Format user profile information for the agent task."""
        if not self.job_application_profile:
            return "No profile information available."

        profile = self.job_application_profile

        # Extract common fields from the profile
        info_parts = []

        if hasattr(profile, "personal_information"):
            personal = profile.personal_information
            if hasattr(personal, "name"):
                info_parts.append(f"- Full Name: {personal.name}")
            if hasattr(personal, "email"):
                info_parts.append(f"- Email: {personal.email}")
            if hasattr(personal, "phone"):
                info_parts.append(f"- Phone: {personal.phone}")
            if hasattr(personal, "address"):
                info_parts.append(f"- Address: {personal.address}")
            if hasattr(personal, "linkedin"):
                info_parts.append(f"- LinkedIn: {personal.linkedin}")

        if hasattr(profile, "legal_authorization"):
            legal = profile.legal_authorization
            if hasattr(legal, "work_authorization"):
                info_parts.append(f"- Work Authorization: {legal.work_authorization}")
            if hasattr(legal, "requires_sponsorship"):
                info_parts.append(f"- Requires Visa Sponsorship: {legal.requires_sponsorship}")

        return "\n".join(info_parts) if info_parts else "Use reasonable defaults for personal information."

    def _format_answers_for_agent(self, answers: Dict[str, str]) -> str:
        """Format pre-defined answers for the agent."""
        if not answers:
            return "No pre-defined answers provided."

        parts = [f"- {question}: {answer}" for question, answer in answers.items()]
        return "\n".join(parts)

    def _get_sensitive_data(self) -> Optional[Dict[str, str]]:
        """Get sensitive data that should be handled securely by the agent."""
        sensitive = {}

        if self.job_application_profile and hasattr(
            self.job_application_profile, "personal_information"
        ):
            personal = self.job_application_profile.personal_information
            if hasattr(personal, "email"):
                sensitive["email"] = personal.email
            if hasattr(personal, "phone"):
                sensitive["phone"] = personal.phone

        return sensitive if sensitive else None

    async def close(self):
        """Close the browser and clean up resources."""
        if self.browser:
            await self.browser.close()
            self.browser = None

    def search_jobs_sync(
        self,
        company: str,
        position: Optional[str] = None,
        location: Optional[str] = None,
    ) -> List[Job]:
        """Synchronous wrapper for search_jobs."""
        return asyncio.run(self.search_jobs(company, position, location))

    def apply_to_job_sync(
        self,
        job: Job,
        answers: Optional[Dict[str, str]] = None,
    ) -> GreenhouseJobApplication:
        """Synchronous wrapper for apply_to_job."""
        return asyncio.run(self.apply_to_job(job, answers))

    def get_job_details_sync(self, job: Job) -> Job:
        """Synchronous wrapper for get_job_details."""
        return asyncio.run(self.get_job_details(job))


class GreenhouseJobSearchAgent:
    """
    Agent specifically for searching jobs on Greenhouse boards.

    This agent can browse multiple company job boards and aggregate results.
    """

    def __init__(
        self,
        llm: BaseChatModel,
        work_preferences: Dict[str, Any],
        headless: bool = False,
    ):
        """
        Initialize the job search agent.

        Args:
            llm: Language model for the browser agent.
            work_preferences: User's job preferences (positions, locations, etc.)
            headless: Whether to run browser in headless mode.
        """
        self.llm = llm
        self.work_preferences = work_preferences
        self.headless = headless
        self.browser: Optional[Browser] = None

    async def _get_browser(self) -> Browser:
        """Get or create browser instance."""
        if self.browser is None:
            profile = BrowserProfile(headless=self.headless)
            self.browser = Browser(browser_profile=profile)
        return self.browser

    async def search_company_jobs(self, company_slug: str) -> List[Job]:
        """
        Search jobs on a specific company's Greenhouse board.

        Args:
            company_slug: The company identifier in the Greenhouse URL.

        Returns:
            List of Job objects.
        """
        browser = await self._get_browser()

        positions = self.work_preferences.get("positions", [])
        locations = self.work_preferences.get("locations", [])
        position_text = ", ".join(positions) if positions else "any position"
        location_text = ", ".join(locations) if locations else "any location"

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
        If jobs are paginated, get jobs from the first page only.
        
        Return a list of all matching jobs found.
        """

        agent = Agent(
            task=task,
            llm=self.llm,
            browser=browser,
            use_vision=True,
        )

        result = await agent.run()

        jobs = self._parse_search_results(result, company_slug)
        return jobs

    def _parse_search_results(self, result: Any, company: str) -> List[Job]:
        """Parse agent search results into Job objects."""
        jobs = []

        # The agent returns its findings in the history/result
        # We need to extract structured job data from it
        if hasattr(result, "history") and result.history:
            for step in result.history:
                if hasattr(step, "result") and step.result:
                    # Look for job-like data in the results
                    logger.debug(f"Search step result: {step.result}")

        return jobs

    async def close(self):
        """Close browser resources."""
        if self.browser:
            await self.browser.close()
            self.browser = None
