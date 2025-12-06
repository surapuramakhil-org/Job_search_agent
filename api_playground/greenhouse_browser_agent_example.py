"""
Example usage of the Greenhouse Browser Agent.

This script demonstrates how to use the AI-powered browser agent
to search for and apply to jobs on Greenhouse job boards.

Prerequisites:
- Set up your LLM API key (e.g., OPENAI_API_KEY environment variable)
- Have a resume file ready for uploads
- Configure your job application profile

Usage:
    python greenhouse_browser_agent_example.py
"""

import asyncio
import os
import sys

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from langchain_openai import ChatOpenAI

from job import Job
from job_portals.greenhouse.browser_agent import (
    GreenhouseBrowserAgent,
    GreenhouseJobSearchAgent,
)


async def example_search_jobs():
    """
    Example: Search for jobs on a company's Greenhouse job board.
    """
    # Initialize the LLM (using OpenAI as example)
    llm = ChatOpenAI(
        model="gpt-4o",
        temperature=0,
    )

    # Set up work preferences
    work_preferences = {
        "positions": ["Software Engineer", "Backend Developer"],
        "locations": ["San Francisco", "Remote"],
    }

    # Create the job search agent
    search_agent = GreenhouseJobSearchAgent(
        llm=llm,
        work_preferences=work_preferences,
        headless=False,  # Set to True for headless browsing
    )

    try:
        # Search for jobs on a specific company's board
        # Replace 'stripe' with the actual company slug from their Greenhouse URL
        company_slug = "stripe"  # Example: boards.greenhouse.io/stripe
        
        print(f"Searching for jobs on {company_slug}'s Greenhouse board...")
        jobs = await search_agent.search_company_jobs(company_slug)
        
        print(f"Found {len(jobs)} matching jobs:")
        for job in jobs:
            print(f"  - {job.title} at {job.company} ({job.location})")
            print(f"    Link: {job.link}")
            
    finally:
        await search_agent.close()


async def example_apply_to_job():
    """
    Example: Apply to a specific job on Greenhouse.
    """
    # Initialize the LLM
    llm = ChatOpenAI(
        model="gpt-4o",
        temperature=0,
    )

    # Create a mock job application profile
    # In practice, you would load this from your configuration
    class MockPersonalInfo:
        name = "John Doe"
        email = "john.doe@example.com"
        phone = "555-123-4567"
        linkedin = "https://linkedin.com/in/johndoe"
        address = "San Francisco, CA"

    class MockLegalAuth:
        work_authorization = "US Citizen"
        requires_sponsorship = False

    class MockProfile:
        personal_information = MockPersonalInfo()
        legal_authorization = MockLegalAuth()

    job_profile = MockProfile()

    # Create the browser agent
    agent = GreenhouseBrowserAgent(
        llm=llm,
        job_application_profile=job_profile,
        resume_path="/path/to/your/resume.pdf",  # Update with actual path
        headless=False,
    )

    try:
        # Create a job object (in practice, this would come from job search)
        job = Job(
            portal="Greenhouse",
            id="12345",
            title="Software Engineer",
            company="exampleco",
            link="https://boards.greenhouse.io/exampleco/jobs/12345",
        )

        # Get job details first
        print(f"Getting details for job: {job.title}")
        job = await agent.get_job_details(job)
        print(f"Job description preview: {job.description[:200]}...")

        # Pre-defined answers for common questions
        answers = {
            "How did you hear about this position?": "Company website",
            "Are you authorized to work in the US?": "Yes",
            "Do you require visa sponsorship?": "No",
        }

        # Apply to the job
        print(f"Applying to job: {job.title}")
        application = await agent.apply_to_job(job, answers=answers)

        print(f"Application status: {application.status}")
        if application.error_message:
            print(f"Error: {application.error_message}")

    finally:
        await agent.close()


async def example_full_workflow():
    """
    Example: Complete workflow from search to application.
    """
    # Initialize LLM
    llm = ChatOpenAI(
        model="gpt-4o",
        temperature=0,
    )

    work_preferences = {
        "positions": ["Software Engineer"],
        "locations": ["Remote"],
    }

    # Step 1: Search for jobs
    search_agent = GreenhouseJobSearchAgent(
        llm=llm,
        work_preferences=work_preferences,
        headless=False,
    )

    try:
        # Find jobs from multiple companies
        companies = ["stripe", "airbnb", "figma"]
        all_jobs = []
        
        for company in companies:
            print(f"Searching {company}'s job board...")
            jobs = await search_agent.search_company_jobs(company)
            all_jobs.extend(jobs)
            print(f"  Found {len(jobs)} jobs")

        print(f"\nTotal jobs found: {len(all_jobs)}")

        # Step 2: Apply to suitable jobs (mock application for demo)
        if all_jobs:
            print("\nTo apply to jobs, set up your job application profile and resume path.")
            print("See example_apply_to_job() for details.")

    finally:
        await search_agent.close()


def main():
    """Main entry point for examples."""
    print("Greenhouse Browser Agent Examples")
    print("=" * 50)
    print("\nAvailable examples:")
    print("1. Search jobs on a company's Greenhouse board")
    print("2. Apply to a specific job")
    print("3. Full workflow (search + apply)")
    print("\nNote: These examples require:")
    print("- OPENAI_API_KEY environment variable set")
    print("- Chrome/Chromium browser installed")
    print("- For applying: A resume file and job application profile")

    # Uncomment one of the following to run an example:
    # asyncio.run(example_search_jobs())
    # asyncio.run(example_apply_to_job())
    # asyncio.run(example_full_workflow())
    
    print("\nTo run an example, uncomment the desired function call in main()")


if __name__ == "__main__":
    main()
