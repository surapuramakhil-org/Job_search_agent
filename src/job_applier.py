import base64
from calendar import c
import json
from math import log
from operator import is_
import os
import random
import re
import time
import traceback
from typing import List, Optional, Any, Tuple

from httpx import HTTPStatusError
from loguru import logger
from regex import W
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase.pdfmetrics import stringWidth

from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from config import ANSWERS_CACHE_FILE, CACHE
from custom_exception import JobNotSuitableException, JobSkipException
from jobContext import JobContext
from job_application import JobApplication
from job_application_saver import ApplicationSaver
import job_application_saver
from job_portals.application_form_elements import SelectQuestion, TextBoxQuestionType
from job_portals.base_job_portal import BaseJobPage, BaseJobPortal


from job import Job, JobState
from llm.ai_answerer import AiAnswerer
from utils import browser_utils, time_utils


def question_already_exists_in_data(question: str, data: List[dict]) -> bool:
    """
    Check if a question already exists in the data list.

    Args:
        question: The question text to search for
        data: List of question dictionaries to search through

    Returns:
        bool: True if question exists, False otherwise
    """
    return any(item["question"] == question for item in data)


class AIHawkJobApplier:
    def __init__(
        self,
        job_portal: BaseJobPortal,
        resume_dir: Optional[str],
        set_old_answers: List[Tuple[str, str, str]],
        gpt_answerer: AiAnswerer,
        work_preferences: dict,
        resume_generator_manager,
    ):
        logger.debug("Initializing AIHawkEasyApplier")
        if resume_dir is None or not os.path.exists(resume_dir):
            resume_dir = None
        self.job_page = job_portal.job_page
        self.job_application_page = job_portal.application_page
        self.job_portal = job_portal
        self.resume_path = resume_dir
        self.set_old_answers = set_old_answers
        self.gpt_answerer = gpt_answerer
        self.resume_generator_manager = resume_generator_manager
        self.answers_cache = self._load_answers_from_json()
        self.current_job : Job | None = None
        self.work_preferences = work_preferences
        self.keywords_whitelist = work_preferences.get("keywords_whitelist", [])
        logger.debug("AIHawkEasyApplier initialized successfully")

    def _load_answers_from_json(self) -> List[dict]:
        output_file = ANSWERS_CACHE_FILE
        logger.debug(f"Loading questions from JSON file: {output_file}")
        try:
            with open(output_file, "r") as f:
                try:
                    data = json.load(f)
                    if not isinstance(data, list):
                        raise ValueError(
                            "JSON file format is incorrect. Expected a list of questions."
                        )
                except json.JSONDecodeError:
                    logger.error("JSON decoding failed")
                    data = []
            logger.debug("Questions loaded successfully from JSON")
            return data
        except FileNotFoundError:
            logger.warning("JSON file not found, returning empty list")
            return []
        except Exception:
            tb_str = traceback.format_exc()
            logger.error(f"Error loading questions data from JSON file: {tb_str}")
            raise Exception(
                f"Error loading questions data from JSON file: \nTraceback:\n{tb_str}"
            )

    def apply_to_job(self, job: Job) -> None:
        """
        Starts the process of applying to a job.
        :param job: A job object with the job details.
        :return: None
        """
        logger.debug(f"Applying to job: {job}")
        try:
            self.job_apply(job)
            logger.info(f"Successfully applied to job: {job.title}")
        except Exception as e:
            logger.error(f"Failed to apply to job: {job.title}, error: {str(e)}")
            raise e

    def job_apply(self, job: Job):

        self.job_page.goto_job_page(job)

        if job.job_state in {JobState.APPLIED.value, JobState.CONTINUE.value}:
            raise JobSkipException(f"Job state is {job.job_state}")

        logger.debug(f"Starting job application for job: {job}")
        job_context = JobContext()
        job_context.job = job
        job_context.job_application = JobApplication(job)
        time_utils.short_sleep()

        try:

            job_description = self.job_page.get_job_description(job)
            logger.debug(f"Job description set: {job_description[:100]}")
            job.set_job_description(job_description)

            recruiter_link = self.job_page.get_recruiter_link()
            job.set_recruiter_link(recruiter_link)

            job.location = self.job_page.get_location()
            job.categories = self.job_page.get_job_categories()

            self.current_job = job

            logger.debug("Passing job information to GPT Answerer")
            self.gpt_answerer.set_job(job)

            keywords_whitelist_check, _  = self._check_keywords_whitelist(job)

            if not self.gpt_answerer.is_work_preferences_match(job, self.work_preferences):
                logger.debug(f"Work preferences didn't match for {job.title} at {job.company}")
                raise JobNotSuitableException(f"Work preferences didn't match, job: {job.title} at {job.company }")
            
            if not keywords_whitelist_check:
                logger.debug(f"Job description keywords not found for {job.title} at {job.company}")
                raise JobNotSuitableException(f"Keywords whitelist didn't pass, keywords:{self.keywords_whitelist} Job Description {job.description} ")

            is_suitable, score, reasoning = self.gpt_answerer.is_job_suitable(self.work_preferences)

            if not is_suitable:
                raise JobNotSuitableException(f"Job is not suitable, got score {score}, reasoning: {reasoning}")

            self.job_page.click_apply_button(job_context)
            time_utils.short_sleep()

            logger.debug("Filling out application form")
            self._fill_application_form(job_context)
            logger.debug(
                f"Job application process completed successfully for job: {job}"
            )

        except Exception as e:

            tb_str = traceback.format_exc()
            logger.error(f"Failed to apply to job: {job}, error: {tb_str}")

            if self.job_application_page.has_save_button():
                logger.debug("marking save in job application page")
                self.job_application_page.save()
            
            logger.debug("Saving application details")
            ApplicationSaver.save(job_context.job_application, is_failed=True)

            raise e
    
    def _check_keywords_whitelist(self, job : Job) -> Tuple[bool, Optional[str]]:
        """
        Check if job description contains any of the specified keywords.
        
        Returns:
            bool: True if any keyword is found in description, False otherwise
        """
        logger.debug(f"Checking job description for keywords: {self.keywords_whitelist}")
        try:
            
            # Get the full description text
            description_text = job.description.lower()

            if self.keywords_whitelist == []:
                logger.debug("No keywords specified for job description check")
                return True, None
            
            # Check if any keyword exists in the description
            for keyword in self.keywords_whitelist:
                if keyword.lower() in description_text:
                    logger.debug(f"Found keyword '{keyword}' in job description")
                    return True, None
                    
            logger.debug("No matching keywords found in job description")
            return False, "No matching keywords found in job description"
            
        except Exception as e:
            logger.error(f"Error checking job description keywords: {e}")
            return True, None

    def _fill_application_form(self, job_context: JobContext):
        job = job_context.job
        job_application = job_context.job_application
        logger.debug(f"Filling out application form for job: {job}")

        while True:
            self.fill_up(job_context)
            browser_utils.handle_security_checks()

            if self.job_application_page.has_next_button():
                self.job_application_page.click_next_button()
                self.job_application_page.handle_errors()
                time_utils.short_sleep()

            elif self.job_application_page.has_submit_button():
                self.job_application_page.click_submit_button()
                ApplicationSaver.save(job_application)
                browser_utils.handle_security_checks()
                logger.debug("Application form submitted")

                time_utils.short_sleep()
                
                if not self.job_application_page.application_submission_confirmation():
                    raise Exception(f"Application submission confirmation is missing for job: {job}")
                
                logger.debug("Application submission confirmaed")

                return
            
            else:
                logger.warning(f"submit button not found, discarding application {job}")
                raise Exception(f" No next or submit button found, discarding application {job}")

    def fill_up(self, job_context: JobContext) -> None:
        job = job_context.job
        logger.debug(f"Filling up form sections for job: {job}")

        form_sections = self.job_application_page.get_form_sections()

        try:
            for form_section in form_sections:
                self._process_form_section(form_section=form_section, job_context=job_context)

        except Exception as e:
            logger.error(
                f"Failed to fill up form sections: {e} {traceback.format_exc()}"
            )
            raise e

    def _handle_upload_fields(
        self, element: WebElement, job_context: JobContext
    ) -> None:
        logger.debug("Handling upload field")

        file_upload_element_heading = self.job_application_page.get_upload_element_heading(element)

        logger.debug(f"File upload element heading: {file_upload_element_heading}")

        output = self.gpt_answerer.determine_resume_or_cover(
            file_upload_element_heading
        )

        logger.debug(f"Output from LLM: {output}")

        if "resume" in output:
            logger.debug("Uploading resume")
            if self.resume_path is not None and os.path.isfile(self.resume_path):
                resume_file_path = os.path.abspath(self.resume_path)
                self.job_application_page.upload_file(element, resume_file_path)
                job_context.job.resume_path = resume_file_path
                job_context.job_application.resume_path = resume_file_path
                job_context.job_application.save_application_data({
                    "type": "resume",
                    "question": "Resume",
                    "answer": resume_file_path
                })
                logger.debug(f"Resume uploaded from path: {resume_file_path}")
            else:
                logger.debug(
                    "Resume path not found or invalid, generating new resume"
                )
                self._create_and_upload_resume(element, job_context)

        elif "cover" in output:
            logger.debug("Uploading cover letter")
            self._create_and_upload_cover_letter(element, job_context)

        logger.debug("Finished handling upload field")

    def _create_and_upload_resume(self, element, job_context: JobContext):
        job = job_context.job
        job_application = job_context.job_application
        logger.debug("Starting the process of creating and uploading resume.")
        folder_path = "generated_cv"

        try:
            if not os.path.exists(folder_path):
                logger.debug(f"Creating directory at path: {folder_path}")
            os.makedirs(folder_path, exist_ok=True)
        except Exception as e:
            logger.error(f"Failed to create directory: {folder_path}. Error: {e}")
            raise

        while True:
            try:
                timestamp = int(time.time())
                file_path_pdf = os.path.join(folder_path, f"CV_{timestamp}.pdf")
                logger.debug(f"Generated file path for resume: {file_path_pdf}")

                logger.debug(f"Generating resume for job: {job.title} at {job.company}")
                resume_pdf_base64 = self.resume_generator_manager.pdf_base64(
                    job_description_text=job.description
                )
                with open(file_path_pdf, "xb") as f:
                    f.write(base64.b64decode(resume_pdf_base64))
                logger.debug(
                    f"Resume successfully generated and saved to: {file_path_pdf}"
                )

                break
            except HTTPStatusError as e:
                if e.response.status_code == 429:

                    retry_after = e.response.headers.get("retry-after")
                    retry_after_ms = e.response.headers.get("retry-after-ms")

                    if retry_after:
                        wait_time = int(retry_after)
                        logger.warning(
                            f"Rate limit exceeded, waiting {wait_time} seconds before retrying..."
                        )
                    elif retry_after_ms:
                        wait_time = int(retry_after_ms) / 1000.0
                        logger.warning(
                            f"Rate limit exceeded, waiting {wait_time} milliseconds before retrying..."
                        )
                    else:
                        wait_time = 20
                        logger.warning(
                            f"Rate limit exceeded, waiting {wait_time} seconds before retrying..."
                        )

                    time.sleep(wait_time)
                else:
                    logger.error(f"HTTP error: {e}")
                    raise

            except Exception as e:
                logger.error(f"Failed to generate resume: {e}")
                tb_str = traceback.format_exc()
                logger.error(f"Traceback: {tb_str}")
                if "RateLimitError" in str(e):
                    logger.warning("Rate limit error encountered, retrying...")
                    time.sleep(20)
                else:
                    raise

        file_size = os.path.getsize(file_path_pdf)
        max_file_size = 2 * 1024 * 1024  # 2 MB
        logger.debug(f"Resume file size: {file_size} bytes")
        if file_size > max_file_size:
            logger.error(f"Resume file size exceeds 2 MB: {file_size} bytes")
            raise ValueError("Resume file size exceeds the maximum limit of 2 MB.")

        allowed_extensions = {".pdf", ".doc", ".docx"}
        file_extension = os.path.splitext(file_path_pdf)[1].lower()
        logger.debug(f"Resume file extension: {file_extension}")
        if file_extension not in allowed_extensions:
            logger.error(f"Invalid resume file format: {file_extension}")
            raise ValueError(
                "Resume file format is not allowed. Only PDF, DOC, and DOCX formats are supported."
            )

        try:
            logger.debug(f"Uploading resume from path: {file_path_pdf}")
            element.send_keys(os.path.abspath(file_path_pdf))
            job.resume_path = os.path.abspath(file_path_pdf)
            job_application.resume_path = os.path.abspath(file_path_pdf)
            job_application.save_application_data({
                "type": "resume",
                "question": "Resume",
                "answer": os.path.abspath(file_path_pdf)
            })
            time.sleep(2)
            logger.debug(f"Resume created and uploaded successfully: {file_path_pdf}")
        except Exception as e:
            tb_str = traceback.format_exc()
            logger.error(f"Resume upload failed: {tb_str}")
            raise Exception(f"Upload failed: \nTraceback:\n{tb_str}")

    def _create_and_upload_cover_letter(
        self, element: WebElement, job_context: JobContext
    ) -> None:
        job = job_context.job
        logger.debug("Starting the process of creating and uploading cover letter.")

        cover_letter_text = self.gpt_answerer.answer_question_textual_wide_range(
            "Write a cover letter"
        )

        folder_path = "generated_cv"

        try:

            if not os.path.exists(folder_path):
                logger.debug(f"Creating directory at path: {folder_path}")
            os.makedirs(folder_path, exist_ok=True)
        except Exception as e:
            logger.error(f"Failed to create directory: {folder_path}. Error: {e}")
            raise

        while True:
            try:
                timestamp = int(time.time())
                file_path_pdf = os.path.join(
                    folder_path, f"Cover_Letter_{timestamp}.pdf"
                )
                logger.debug(f"Generated file path for cover letter: {file_path_pdf}")

                c = canvas.Canvas(file_path_pdf, pagesize=A4)
                page_width, page_height = A4
                text_object = c.beginText(50, page_height - 50)
                text_object.setFont("Helvetica", 12)

                max_width = page_width - 100
                bottom_margin = 50
                available_height = page_height - bottom_margin - 50

                def split_text_by_width(text, font, font_size, max_width):
                    wrapped_lines = []
                    for line in text.splitlines():

                        if stringWidth(line, font, font_size) > max_width:
                            words = line.split()
                            new_line = ""
                            for word in words:
                                if (
                                    stringWidth(new_line + word + " ", font, font_size)
                                    <= max_width
                                ):
                                    new_line += word + " "
                                else:
                                    wrapped_lines.append(new_line.strip())
                                    new_line = word + " "
                            wrapped_lines.append(new_line.strip())
                        else:
                            wrapped_lines.append(line)
                    return wrapped_lines

                lines = split_text_by_width(
                    cover_letter_text, "Helvetica", 12, max_width
                )

                for line in lines:
                    text_height = text_object.getY()
                    if text_height > bottom_margin:
                        text_object.textLine(line)
                    else:

                        c.drawText(text_object)
                        c.showPage()
                        text_object = c.beginText(50, page_height - 50)
                        text_object.setFont("Helvetica", 12)
                        text_object.textLine(line)

                c.drawText(text_object)
                c.save()
                logger.debug(
                    f"Cover letter successfully generated and saved to: {file_path_pdf}"
                )

                break
            except Exception as e:
                logger.error(f"Failed to generate cover letter: {e}")
                tb_str = traceback.format_exc()
                logger.error(f"Traceback: {tb_str}")
                raise

        file_size = os.path.getsize(file_path_pdf)
        max_file_size = 2 * 1024 * 1024  # 2 MB
        logger.debug(f"Cover letter file size: {file_size} bytes")
        if file_size > max_file_size:
            logger.error(f"Cover letter file size exceeds 2 MB: {file_size} bytes")
            raise ValueError(
                "Cover letter file size exceeds the maximum limit of 2 MB."
            )

        allowed_extensions = {".pdf", ".doc", ".docx"}
        file_extension = os.path.splitext(file_path_pdf)[1].lower()
        logger.debug(f"Cover letter file extension: {file_extension}")
        if file_extension not in allowed_extensions:
            logger.error(f"Invalid cover letter file format: {file_extension}")
            raise ValueError(
                "Cover letter file format is not allowed. Only PDF, DOC, and DOCX formats are supported."
            )

        try:

            logger.debug(f"Uploading cover letter from path: {file_path_pdf}")
            element.send_keys(os.path.abspath(file_path_pdf))
            job.cover_letter_path = os.path.abspath(file_path_pdf)
            job_context.job_application.cover_letter_path = os.path.abspath(
                file_path_pdf
            )
            job_context.job_application.save_application_data({
                "type": "cover_letter",
                "question": "Cover Letter",
                "answer": os.path.abspath(file_path_pdf)
            })
            time.sleep(2)
            logger.debug(
                f"Cover letter created and uploaded successfully: {file_path_pdf}"
            )
        except Exception as e:
            tb_str = traceback.format_exc()
            logger.error(f"Cover letter upload failed: {tb_str}")
            raise Exception(f"Upload failed: \nTraceback:\n{tb_str}")

    def _process_form_section(self, job_context: JobContext, form_section: WebElement) -> None:
        logger.debug("Filling additional questions")
        form_elements = self.job_application_page.get_input_elements(form_section=form_section)
        for form_element in form_elements:
            logger.debug(f"Processing form element with text: {form_element.text}")
            job_context.job_application.add_question_to_form(form_element.text)
            self._process_form_element(job_context, form_element)

    def _process_form_element(
        self, job_context: JobContext, form_element: WebElement
    ) -> None:
        """
        application page will be unified into 4 categories
        1. file uploads
        2. Agree questions like terms of service (checkbox boxes where unckeck is considered as not agreed)
        3. text inputs (number, text, email, long answer, short answer, textfield with limits)
        4. select options (radio, dropdown, check boxes like options)
        """

        logger.debug("Processing form section")

        browser_utils.handle_security_checks()
        time_utils.tiny_sleep()

        self.job_application_page.wait_until_ready()

        if self.job_application_page.is_upload_field(form_element):
            self._handle_upload_fields(form_element, job_context)
            return
        
        if self.job_application_page.is_terms_of_service(form_element):
            logger.debug("Handled terms of service")
            self.job_application_page.accept_terms_of_service(form_element)
            return

        if self.job_application_page.is_radio_question(form_element):
            radio_question = self.job_application_page.web_element_to_radio_question(
                form_element
            )
            self._handle_radio_question(job_context, radio_question, form_element)
            logger.debug("Handled radio button")
            return

        if self.job_application_page.is_textbox_question(form_element):
            self._handle_textbox_question(job_context, form_element)
            logger.debug("Handled textbox question")
            return

        if self.job_application_page.is_dropdown_question(form_element):
            self._handle_dropdown_question(job_context, form_element)
            logger.debug("Handled dropdown question")
            return
        
        logger.warning("No matching form element found")            

    #TODO: Enhance this method to handle multi-select questions
    def _handle_radio_question(
        self,
        job_context: JobContext,
        radio_question: SelectQuestion,
        section: WebElement,
    ) -> None:
        job_application = job_context.job_application

        question_text = radio_question.question
        options = radio_question.options

        existing_answer = self._find_existing_answer(question_text, "radio")

        if existing_answer:
            self.job_application_page.select_radio_option(
                section, existing_answer["answer"]
            )
            job_application.save_application_data(existing_answer)
            logger.debug("Selected existing radio answer")
            return

        answer = self.gpt_answerer.answer_question_from_options(question_text, options)
        self._save_answer_to_json(
            {"type": "radio", "question": question_text, "answer": answer}
        )
        self.answers_cache = self._load_answers_from_json()
        job_application.save_application_data(
            {"type": "radio", "question": question_text, "answer": answer}
        )
        self.job_application_page.select_radio_option(section, answer)
        logger.debug("Selected new radio answer")
        return

    def _handle_textbox_question(
        self, job_context: JobContext, element: WebElement
    ) -> None:

        textbox_question = self.job_application_page.web_element_to_textbox_question(
            element
        )

        question_text = textbox_question.question
        question_type = textbox_question.type.value
        is_cover_letter = "cover letter" in question_text.lower()
        is_numeric = textbox_question.type is TextBoxQuestionType.NUMERIC

        existing_answer = None
        if not is_cover_letter:
            existing_answer = self._find_existing_answer(question_text, question_type)

        if existing_answer and not is_cover_letter:
            answer = existing_answer["answer"]
            logger.debug(f"Using existing answer: {answer}")
        else:
            if is_numeric:
                answer = self.gpt_answerer.answer_question_numeric(question_text)
                logger.debug(f"Generated numeric answer: {answer}")
            else:
                answer = self.gpt_answerer.answer_question_textual_wide_range(
                    question_text
                )
                logger.debug(f"Generated textual answer: {answer}")

        if not is_cover_letter and not existing_answer:
            self._save_answer_to_json(
                {"type": question_type, "question": question_text, "answer": answer}
            )
            self.answers_cache = self._load_answers_from_json()
            logger.debug("Saved non-cover letter answer to JSON.")

        self.job_application_page.fill_textbox_question(element, answer)
        logger.debug("Entered answer into the textbox.")

        job_context.job_application.save_application_data(
            {"type": question_type, "question": question_text, "answer": answer}
        )

        return

    def _handle_dropdown_question(
        self, job_context: JobContext, section: WebElement
    ) -> None:
        job_application = job_context.job_application

        dropdown = self.job_application_page.web_element_to_dropdown_question(section)

        question_text = dropdown.question
        options = dropdown.options

        existing_answer = self._find_existing_answer(question_text, "dropdown")

        if existing_answer:
            answer = existing_answer["answer"]
            logger.debug(
                f"Found existing answer for question '{question_text}': {answer}"
            )
        else:
            logger.debug(
                f"No existing answer found, querying model for: {question_text}"
            )
            answer = self.gpt_answerer.answer_question_from_options(
                question_text, options
            )
            self._save_answer_to_json(
                {
                    "type": "dropdown",
                    "question": question_text,
                    "answer": answer,
                }
            )
            self.answers_cache = self._load_answers_from_json()

        job_application.save_application_data(
            {
                "type": "dropdown",
                "question": question_text,
                "answer": answer,
            }
        )
        self.job_application_page.select_dropdown_option(section, answer)
        logger.debug(f"Selected new dropdown answer: {answer}")
        return
    
    def _save_answer(self, answer_data: dict) -> None:
        self._save_answer_to_json(answer_data)

    def _save_answer_to_json(self, question_data: dict) -> None:
        output_file = ANSWERS_CACHE_FILE
        question_data["question"] = self._sanitize_text(question_data["question"])

        logger.debug(f"Checking if question data already exists: {question_data}")
        try:
            with open(output_file, "r+") as f:
                try:
                    data = json.load(f)
                    if not isinstance(data, list):
                        raise ValueError(
                            "JSON file format is incorrect. Expected a list of questions."
                        )
                except json.JSONDecodeError:
                    logger.error("JSON decoding failed")
                    data = []

                should_be_saved: bool = not question_already_exists_in_data(
                    question_data["question"], data
                ) and not self.answer_contians_company_name(question_data["answer"])

                if should_be_saved:
                    logger.debug("New question found, appending to JSON")
                    data.append(question_data)
                    f.seek(0)
                    json.dump(data, f, indent=4)
                    f.truncate()
                    logger.debug("Question data saved successfully to JSON")
                else:
                    logger.debug("Question already exists, skipping save")
        except FileNotFoundError:
            logger.warning("JSON file not found, creating new file")
            with open(output_file, "w") as f:
                json.dump([question_data], f, indent=4)
            logger.debug("Question data saved successfully to new JSON file")
        except Exception:
            tb_str = traceback.format_exc()
            logger.error(f"Error saving questions data to JSON file: {tb_str}")
            raise Exception(
                f"Error saving questions data to JSON file: \nTraceback:\n{tb_str}"
            )

    def _sanitize_text(self, text: str) -> str:
        sanitized_text = text.lower().strip().replace('"', "").replace("\\", "")
        sanitized_text = (
            re.sub(r"[\x00-\x1F\x7F]", "", sanitized_text)
            .replace("\n", " ")
            .replace("\r", "")
            .rstrip(",")
        )
        logger.debug(f"Sanitized text: {sanitized_text}")
        return sanitized_text

    def _find_existing_answer(self, question_text: str, question_type: str) -> Optional[dict]:
        if not CACHE:
            logger.trace("Cache is disabled, not checking for existing answers")
            return None

        current_question_sanitized = self._sanitize_text(question_text)
        for item in self.answers_cache:
            if (
                current_question_sanitized == self._sanitize_text(item["question"])
                and item["type"] == question_type
            ):
                return item
        return None

    def answer_contians_company_name(self, answer: Any) -> bool:
        return (
            isinstance(answer, str)
            and self.current_job is not None
            and self.current_job.company is not None
            and self.current_job.company in answer
        )
