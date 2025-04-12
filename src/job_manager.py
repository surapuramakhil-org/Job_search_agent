import json
import os
import random
import re
import time
import traceback
from datetime import datetime
from itertools import product
from pathlib import Path

from inputimeout import inputimeout, TimeoutOccurred
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC

import config
from constants import WORK_PREFERENCES
from custom_exception import JobNotSuitableException
from job import Job
from job_applier import AIHawkJobApplier
from job_application_profile import WorkPreferences
from job_portals.base_job_portal import BaseJobPortal
from logger import logger
from regex_utils import look_ahead_patterns
import utils.browser_utils as browser_utils
import utils.time_utils


class EnvironmentKeys:
    def __init__(self):
        logger.info("Initializing EnvironmentKeys")
        self.skip_apply = self._read_env_key_bool("SKIP_APPLY")
        self.disable_description_filter = self._read_env_key_bool(
            "DISABLE_DESCRIPTION_FILTER"
        )
        logger.info(
            f"EnvironmentKeys initialized: skip_apply={self.skip_apply}, disable_description_filter={self.disable_description_filter}"
        )

    @staticmethod
    def _read_env_key(key: str) -> str:
        value = os.getenv(key, "")
        logger.debug(f"Read environment key {key}: {value}")
        return value

    @staticmethod
    def _read_env_key_bool(key: str) -> bool:
        value = os.getenv(key) == "True"
        logger.debug(f"Read environment key {key} as bool: {value}")
        return value


class AIHawkJobManager:
    def __init__(self, job_portal: BaseJobPortal):
        logger.info("Initializing AIHawkJobManager")
        self.job_portal = job_portal
        self.set_old_answers = set()
        self.easy_applier_component = None
        logger.info("AIHawkJobManager initialized successfully")

    def set_parameters(self, parameters):
        logger.info("Setting parameters for AIHawkJobManager")
        self.workPreferences = parameters.get(WORK_PREFERENCES)
        self.company_blacklist = self.workPreferences.get("company_blacklist", []) or []
        self.title_blacklist = self.workPreferences.get("title_blacklist", []) or []
        self.location_blacklist = (
            self.workPreferences.get("location_blacklist", []) or []
        )
        self.positions = self.workPreferences.get("positions", [])
        self.locations = self.workPreferences.get("locations", [])
        self.seen_jobs = []
        self.keywords_whitelist = (
            self.workPreferences.get("keywords_whitelist", []) or []
        )

        self.min_applicants = config.JOB_MIN_APPLICATIONS
        self.max_applicants = config.JOB_MAX_APPLICATIONS

        # Generate regex patterns from blacklist lists
        self.title_blacklist_patterns = look_ahead_patterns(self.title_blacklist)
        self.company_blacklist_patterns = look_ahead_patterns(self.company_blacklist)
        self.location_blacklist_patterns = look_ahead_patterns(self.location_blacklist)

        resume_path = parameters.get("uploads", {}).get("resume", None)
        self.resume_path = (
            Path(resume_path) if resume_path and Path(resume_path).exists() else None
        )
        self.output_file_directory = Path(parameters["outputFileDirectory"])
        self.env_config = EnvironmentKeys()
        logger.info("Parameters set successfully")

    def set_gpt_answerer(self, gpt_answerer):
        logger.info("Setting GPT answerer")
        self.gpt_answerer = gpt_answerer

    def set_resume_generator_manager(self, resume_generator_manager):
        logger.info("Setting resume generator manager")
        self.resume_generator_manager = resume_generator_manager

    def start_collecting_data(self):
        searches = list(product(self.positions, self.locations))
        random.shuffle(searches)
        page_sleep = 0
        minimum_time = 60 * 5
        minimum_page_time = time.time() + minimum_time

        for position, location in searches:
            location_url = "&location=" + location
            job_page_number = -1
            logger.info(
                f"Collecting data for {position} in {location}.", color="yellow"
            )
            try:
                while True:
                    page_sleep += 1
                    job_page_number += 1
                    logger.info(f"Going to job page {job_page_number}", color="yellow")
                    self.job_portal.jobs_page.next_job_page(
                        position, location_url, job_page_number
                    )
                    utils.time_utils.medium_sleep()
                    logger.info(
                        "Starting the collecting process for this page", color="yellow"
                    )
                    self.read_jobs()
                    logger.info(
                        "Collecting data on this page has been completed!",
                        color="yellow",
                    )

                    time_left = minimum_page_time - time.time()
                    if time_left > 0:
                        logger.info(
                            f"Sleeping for {time_left} seconds.", color="yellow"
                        )
                        time.sleep(time_left)
                        minimum_page_time = time.time() + minimum_time
                    if page_sleep % 5 == 0:
                        sleep_time = random.randint(1, 5)
                        logger.info(
                            f"Sleeping for {sleep_time / 60} minutes.", color="yellow"
                        )
                        time.sleep(sleep_time)
                        page_sleep += 1
            except Exception:
                pass
            time_left = minimum_page_time - time.time()
            if time_left > 0:
                logger.info(f"Sleeping for {time_left} seconds.", color="yellow")
                time.sleep(time_left)
                minimum_page_time = time.time() + minimum_time
            if page_sleep % 5 == 0:
                sleep_time = random.randint(50, 90)
                logger.info(f"Sleeping for {sleep_time / 60} minutes.", color="yellow")
                time.sleep(sleep_time)
                page_sleep += 1

    def start_applying(self):
        logger.info("Starting job application process")
        self.easy_applier_component = AIHawkJobApplier(
            self.job_portal,
            self.resume_path,
            self.set_old_answers,
            self.gpt_answerer,
            self.workPreferences,
            self.resume_generator_manager,
        )
        searches = list(product(self.positions, self.locations))
        random.shuffle(searches)
        page_sleep = 0
        minimum_time = config.MINIMUM_WAIT_TIME_IN_SECONDS
        minimum_page_time = time.time() + minimum_time

        for position, location in searches:
            job_page_number = -1
            logger.info(f"Starting the search for {position} in {location}.")

            try:
                while True:
                    page_sleep += 1
                    job_page_number += 1
                    logger.info(f"Going to job page {job_page_number}")
                    self.job_portal.jobs_page.next_job_page(
                        position, location, job_page_number
                    )
                    utils.time_utils.medium_sleep()
                    logger.info("Starting the application process for this page...")

                    try:
                        jobs = self.job_portal.jobs_page.get_jobs_from_page(scroll=True)
                        if not jobs:
                            logger.info(
                                "No more jobs found on this page. Exiting loop."
                            )
                            break
                    except Exception as e:
                        logger.error(f"Failed to retrieve jobs: {e}")
                        break

                    try:
                        self.apply_jobs()
                    except Exception as e:
                        logger.error(
                            f"Error during job application: {e} {traceback.format_exc()}"
                        )
                        continue

                    logger.info("Applying to jobs on this page has been completed!")

                    time_left = minimum_page_time - time.time()

                    # Ask user if they want to skip waiting, with timeout
                    if time_left > 0:
                        try:
                            user_input = (
                                inputimeout(
                                    prompt=f"Sleeping for {time_left} seconds. Press 'y' to skip waiting. Timeout 60 seconds : ",
                                    timeout=60,
                                )
                                .strip()
                                .lower()
                            )
                        except TimeoutOccurred:
                            user_input = ""  # No input after timeout
                        if user_input == "y":
                            logger.info("User chose to skip waiting.")
                        else:
                            logger.info(
                                f"Sleeping for {time_left} seconds as user chose not to skip."
                            )
                            time.sleep(time_left)

                    minimum_page_time = time.time() + minimum_time

                    if page_sleep % 5 == 0:
                        sleep_time = random.randint(5, 34)
                        try:
                            user_input = (
                                inputimeout(
                                    prompt=f"Sleeping for {sleep_time / 60} minutes. Press 'y' to skip waiting. Timeout 60 seconds : ",
                                    timeout=60,
                                )
                                .strip()
                                .lower()
                            )
                        except TimeoutOccurred:
                            user_input = ""  # No input after timeout
                        if user_input == "y":
                            logger.info("User chose to skip waiting.")
                        else:
                            logger.info(f"Sleeping for {sleep_time} seconds.")
                            time.sleep(sleep_time)
                        page_sleep += 1
            except Exception as e:
                logger.error(f"Unexpected error during job search: {e}")
                continue

            time_left = minimum_page_time - time.time()

            if time_left > 0:
                try:
                    user_input = (
                        inputimeout(
                            prompt=f"Sleeping for {time_left} seconds. Press 'y' to skip waiting. Timeout 60 seconds : ",
                            timeout=60,
                        )
                        .strip()
                        .lower()
                    )
                except TimeoutOccurred:
                    user_input = ""  # No input after timeout
                if user_input == "y":
                    logger.info("User chose to skip waiting.")
                else:
                    logger.info(
                        f"Sleeping for {time_left} seconds as user chose not to skip."
                    )
                    time.sleep(time_left)

            minimum_page_time = time.time() + minimum_time

            if page_sleep % 5 == 0:
                sleep_time = random.randint(50, 90)
                try:
                    user_input = (
                        inputimeout(
                            prompt=f"Sleeping for {sleep_time / 60} minutes. Press 'y' to skip waiting: ",
                            timeout=60,
                        )
                        .strip()
                        .lower()
                    )
                except TimeoutOccurred:
                    user_input = ""  # No input after timeout
                if user_input == "y":
                    logger.info("User chose to skip waiting.")
                else:
                    logger.info(f"Sleeping for {sleep_time} seconds.")
                    time.sleep(sleep_time)
                page_sleep += 1

    def read_jobs(self):

        job_element_list = self.job_portal.jobs_page.get_jobs_from_page()
        job_list = [
            self.job_portal.jobs_page.job_tile_to_job(job_element)
            for job_element in job_element_list
        ]
        for job in job_list:
            if self.is_blacklisted(job.title, job.company, job.link, job.location):
                logger.info(
                    f"Blacklisted {job.title} at {job.company} in {job.location}, skipping..."
                )
                self.write_to_file(job, "skipped")
                continue
            try:
                self.write_to_file(job, "data")
            except Exception as e:
                self.write_to_file(job, "failed")
                continue

    def apply_jobs(self):
        job_element_list = self.job_portal.jobs_page.get_jobs_from_page()

        job_list = [
            self.job_portal.jobs_page.job_tile_to_job(job_element)
            for job_element in job_element_list
        ]

        for job in job_list:

            logger.info(f"Starting applicant for job: {job.title} at {job.company}")
            # TODO fix apply threshold
            """
                # Initialize applicants_count as None
                applicants_count = None

                # Iterate over each job insight element to find the one containing the word "applicant"
                for element in job_insight_elements:
                    logger.debug(f"Checking element text: {element.text}")
                    if "applicant" in element.text.lower():
                        # Found an element containing "applicant"
                        applicants_text = element.text.strip()
                        logger.debug(f"Applicants text found: {applicants_text}")

                        # Extract numeric digits from the text (e.g., "70 applicants" -> "70")
                        applicants_count = ''.join(filter(str.isdigit, applicants_text))
                        logger.debug(f"Extracted applicants count: {applicants_count}")

                        if applicants_count:
                            if "over" in applicants_text.lower():
                                applicants_count = int(applicants_count) + 1  # Handle "over X applicants"
                                logger.debug(f"Applicants count adjusted for 'over': {applicants_count}")
                            else:
                                applicants_count = int(applicants_count)  # Convert the extracted number to an integer
                        break

                # Check if applicants_count is valid (not None) before performing comparisons
                if applicants_count is not None:
                    # Perform the threshold check for applicants count
                    if applicants_count < self.min_applicants or applicants_count > self.max_applicants:
                        logger.debug(f"Skipping {job.title} at {job.company}, applicants count: {applicants_count}")
                        self.write_to_file(job, "skipped_due_to_applicants")
                        continue  # Skip this job if applicants count is outside the threshold
                    else:
                        logger.debug(f"Applicants count {applicants_count} is within the threshold")
                else:
                    # If no applicants count was found, log a warning but continue the process
                    logger.warning(
                        f"Applicants count not found for {job.title} at {job.company}, continuing with application.")
            except NoSuchElementException:
                # Log a warning if the job insight elements are not found, but do not stop the job application process
                logger.warning(
                    f"Applicants count elements not found for {job.title} at {job.company}, continuing with application.")
            except ValueError as e:
                # Handle errors when parsing the applicants count
                logger.error(f"Error parsing applicants count for {job.title} at {job.company}: {e}")
            except Exception as e:
                # Catch any other exceptions to ensure the process continues
                logger.error(
                    f"Unexpected error during applicants count processing for {job.title} at {job.company}: {e}")

            # Continue with the job application process regardless of the applicants count check
            """

            if self.is_previously_failed_to_apply(job.link):
                logger.info(
                    f"Previously failed to apply for {job.title} at {job.company}, skipping..."
                )
                continue
            if self.is_blacklisted(job.title, job.company, job.link, job.location):
                logger.info(
                    f"Job blacklisted: {job.title} at {job.company} in {job.location}"
                )
                self.write_to_file(job, "skipped", "Job blacklisted")
                continue
            if self.is_already_applied_to_job(job.title, job.company, job.link):
                self.write_to_file(job, "skipped", "Already applied to this job")
                continue
            if self.is_already_applied_to_company(job.company):
                self.write_to_file(job, "skipped", "Already applied to this company")
                continue

            try:

                self.easy_applier_component.job_apply(job)
                self.write_to_file(job, "success")
                logger.info(f"Applied to job: {job.title} at {job.company}")
            except JobNotSuitableException as e:
                logger.info(
                    f"Job not suitable for application: {job.title} at {job.company}"
                )
                self.write_to_file(job, "skipped", f"{str(e)} {traceback.format_exc()}")
                continue
            except Exception as e:
                logger.error(
                    f"Failed to apply for {job.title} at {job.company}: {str(e)}\n{traceback.format_exc()}"
                )
                self.write_to_file(
                    job,
                    "failed",
                    f"Application error: {str(e)} {traceback.format_exc()}",
                )
                continue

    def write_to_file(self, job: Job, file_name, reason=None):
        logger.info(f"Writing job application result to file: {file_name}")
        pdf_path = Path(job.resume_path).resolve()
        pdf_path = pdf_path.as_uri()
        data = job.__dict__
        data["pdf_path"] = pdf_path
        data["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if reason:
            data["reason"] = reason

        file_path = self.output_file_directory / f"{file_name}.json"
        if not file_path.exists():
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump([data], f, indent=4)
                logger.info(f"Job data written to new file: {file_name}")
        else:
            with open(file_path, "r+", encoding="utf-8") as f:
                try:
                    existing_data = json.load(f)
                except json.JSONDecodeError:
                    logger.error(f"JSON decode error in file: {file_path}")
                    existing_data = []
                existing_data.append(data)
                f.seek(0)
                json.dump(existing_data, f, indent=4)
                f.truncate()
                logger.info(f"Job data appended to existing file: {file_name}")

    def is_blacklisted(self, job_title, company, link, job_location):

        if not job_title or not company or not link or not job_location:
            logger.warning(
                f"One or more input parameters are None or empty: job_title={job_title}, company={company}, link={link}, job_location={job_location}"
            )

        logger.info(
            f"Checking if job is blacklisted: {job_title} at {company} in {job_location}"
        )
        title_blacklisted = any(
            re.search(pattern, job_title, re.IGNORECASE)
            for pattern in self.title_blacklist_patterns
        )
        company_blacklisted = any(
            re.search(pattern, company, re.IGNORECASE)
            for pattern in self.company_blacklist_patterns
        )
        location_blacklisted = any(
            re.search(pattern, job_location, re.IGNORECASE)
            for pattern in self.location_blacklist_patterns
        )

        is_blacklisted = (
            title_blacklisted or company_blacklisted or location_blacklisted
        )
        logger.info(f"Job blacklisted status: {is_blacklisted}")

        return is_blacklisted

    def is_already_applied_to_job(self, job_title, company, link):
        link_seen = link in self.seen_jobs
        if link_seen:
            logger.info(
                f"Already applied to job: {job_title} at {company}, skipping..."
            )
        return link_seen

    def is_already_applied_to_company(self, company):
        if not config.APPLY_ONCE_PER_COMPANY:
            return False

        output_files = ["success.json"]
        for file_name in output_files:
            file_path = self.output_file_directory / file_name
            if file_path.exists():
                with open(file_path, "r", encoding="utf-8") as f:
                    try:
                        existing_data = json.load(f)
                        for applied_job in existing_data:
                            if (
                                applied_job["company"].strip().lower()
                                == company.strip().lower()
                            ):
                                logger.info(
                                    f"Already applied at {company} (once per company policy), skipping..."
                                )
                                return True
                    except json.JSONDecodeError:
                        continue
        return False

    def is_previously_failed_to_apply(self, link):
        file_name = "failed"
        file_path = self.output_file_directory / f"{file_name}.json"

        if not file_path.exists():
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump([], f)

        with open(file_path, "r", encoding="utf-8") as f:
            try:
                existing_data = json.load(f)
            except json.JSONDecodeError:
                logger.error(f"JSON decode error in file: {file_path}")
                return False

        for data in existing_data:
            data_link = data["link"]
            if data_link == link:
                return True

        return False
