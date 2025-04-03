from pydantic import BaseModel, Field
import llm.prompts as prompts
from config import JOB_SUITABILITY_SCORE
from constants import AVAILABILITY, CERTIFICATIONS, COMPANY, COVER_LETTER, EDUCATION_DETAILS, EXPERIENCE_DETAILS, INTERESTS, JOB, JOB_APPLICATION_PROFILE, JOB_DESCRIPTION, LANGUAGES, LEGAL_AUTHORIZATION, OPTIONS, PERSONAL_INFORMATION, PHRASE, PROJECTS, QUESTION, RESUME, RESUME_EDUCATIONS, RESUME_JOBS, RESUME_PROJECTS, RESUME_SECTION, SALARY_EXPECTATIONS, SELF_IDENTIFICATION, TEXT, WORK_PREFERENCES
from job import Job
from job_application_profile import JobApplicationProfile
from llm.llm_manager import AIAdapter, TensorZeroChatModelWrapper


from Levenshtein import distance
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from loguru import logger


import re
import textwrap
import traceback
from copy import deepcopy
from typing import Optional, Tuple


class WorkPreferenceMatch(BaseModel):
        match: bool = Field(description="Whether work preferences match the job")
        reason: str = Field(description="Reason for mismatch if applicable")

class AiAnswerer:

    def __init__(self, config, llm_api_key): # config might be unused now
        self.ai_adapter = AIAdapter(config, llm_api_key)
        self.llm_cheap = TensorZeroChatModelWrapper(self.ai_adapter.model)

    @property
    def job_description(self):
        return self.job.description

    @staticmethod
    def find_best_match(text: str, options: list[str]) -> str:
        logger.debug(f"Finding best match for text: '{text}' in options: {options}")
        distances = [
            (option, distance(text.lower(), option.lower())) for option in options
        ]
        best_option = min(distances, key=lambda x: x[1])[0]
        logger.debug(f"Best match found: {best_option}")
        return best_option

    @staticmethod
    def _remove_placeholders(text: str) -> str:
        logger.debug(f"Removing placeholders from text: {text}")
        text = text.replace("PLACEHOLDER", "")
        return text.strip()

    @staticmethod
    def _preprocess_template_string(template: str) -> str:
        logger.debug("Preprocessing template string")
        return textwrap.dedent(template)

    def set_resume(self, resume):
        logger.debug(f"Setting resume: {resume}")
        self.resume = resume

    def set_job(self, job: Job):
        logger.debug(f"Setting job: {job}")
        self.job = job
        self.job.set_summarize_job_description(
            self.summarize_job_description(self.job.description)
        )

    def set_job_application_profile(self, job_application_profile : JobApplicationProfile):
        logger.debug(f"Setting job application profile: {job_application_profile}")
        self.job_application_profile = job_application_profile

    def _clean_llm_output(self, output: str) -> str:
        return output.replace("*", "").replace("#", "").strip()

    def summarize_job_description(self, text: str) -> str:
        logger.debug(f"Summarizing job description: {text}")
        prompts.summarize_prompt_template = self._preprocess_template_string(
            prompts.summarize_prompt_template
        )
        prompt = ChatPromptTemplate.from_template(prompts.summarize_prompt_template)
        chain = prompt | self.llm_cheap | StrOutputParser()
        raw_output = chain.invoke({TEXT: text})
        output = self._clean_llm_output(raw_output)
        logger.debug(f"Summary generated: {output}")
        return output

    def _create_chain(self, template: str):
        logger.debug(f"Creating chain with template: {template}")
        prompt = ChatPromptTemplate.from_template(template)
        return prompt | self.llm_cheap | StrOutputParser()

    def answer_question_textual_wide_range(self, question: str) -> str:
        logger.debug(f"Answering textual question: {question}")
        chains = {
            PERSONAL_INFORMATION: self._create_chain(
                prompts.personal_information_template
            ),
            SELF_IDENTIFICATION: self._create_chain(
                prompts.self_identification_template
            ),
            LEGAL_AUTHORIZATION: self._create_chain(
                prompts.legal_authorization_template
            ),
            WORK_PREFERENCES: self._create_chain(
                prompts.work_preferences_template
            ),
            EDUCATION_DETAILS: self._create_chain(
                prompts.education_details_template
            ),
            EXPERIENCE_DETAILS: self._create_chain(
                prompts.experience_details_template
            ),
            PROJECTS: self._create_chain(prompts.projects_template),
            AVAILABILITY: self._create_chain(prompts.availability_template),
            SALARY_EXPECTATIONS: self._create_chain(
                prompts.salary_expectations_template
            ),
            CERTIFICATIONS: self._create_chain(
                prompts.certifications_template
            ),
            LANGUAGES: self._create_chain(prompts.languages_template),
            INTERESTS: self._create_chain(prompts.interests_template),
            COVER_LETTER: self._create_chain(prompts.coverletter_template),
        }

        prompt = ChatPromptTemplate.from_template(prompts.determine_section_template)
        chain = prompt | self.llm_cheap | StrOutputParser()
        raw_output = chain.invoke({QUESTION: question})
        output = self._clean_llm_output(raw_output)

        match = re.search(
            r"(Personal information|Self Identification|Legal Authorization|Work Preferences|Education "
            r"Details|Experience Details|Projects|Availability|Salary "
            r"Expectations|Certifications|Languages|Interests|Cover letter)",
            output,
            re.IGNORECASE,
        )
        if not match:
            raise ValueError("Could not extract section name from the response.")

        section_name = match.group(1).lower().replace(" ", "_")

        if section_name == "cover_letter":
            chain = chains.get(section_name)
            raw_output = chain.invoke(
                {
                    RESUME: self.resume,
                    JOB_DESCRIPTION: self.job_description,
                    COMPANY: self.job.company,
                }
            )
            output = self._clean_llm_output(raw_output)
            logger.debug(f"Cover letter generated: {output}")
            return output
        resume_section = getattr(self.resume, section_name, None) or getattr(
            self.job_application_profile, section_name, None
        )
        if resume_section is None:
            logger.error(
                f"Section '{section_name}' not found in either resume or job_application_profile."
            )
            raise ValueError(
                f"Section '{section_name}' not found in either resume or job_application_profile."
            )
        chain = chains.get(section_name)
        if chain is None:
            logger.error(f"Chain not defined for section '{section_name}'")
            raise ValueError(f"Chain not defined for section '{section_name}'")
        raw_output = chain.invoke(
            {RESUME_SECTION: resume_section, QUESTION: question}
        )
        output = self._clean_llm_output(raw_output)
        logger.debug(f"Question answered: {output}")
        return output

    def answer_question_numeric(
        self, question: str, default_experience: str = "3"
    ) -> str:
        logger.debug(f"Answering numeric question: {question}")
        func_template = self._preprocess_template_string(
            prompts.numeric_question_template
        )
        prompt = ChatPromptTemplate.from_template(func_template)
        chain = prompt | self.llm_cheap | StrOutputParser()
        raw_output_str = chain.invoke(
            {
                RESUME_EDUCATIONS: self.resume.education_details,
                RESUME_JOBS: self.resume.experience_details,
                RESUME_PROJECTS: self.resume.projects,
                QUESTION: question,
            }
        )
        output_str = self._clean_llm_output(raw_output_str)
        logger.debug(f"Raw output for numeric question: {output_str}")
        try:
            output = self.extract_number_from_string(output_str)
            logger.debug(f"Extracted number: {output}")
        except ValueError:
            logger.warning(
                f"Failed to extract number, using default experience: {default_experience}"
            )
            output = default_experience
        return output

    def extract_number_from_string(self, output_str):
        logger.debug(f"Extracting number from string: {output_str}")
        numbers = re.findall(r"\d+", output_str)
        if numbers:
            logger.debug(f"Numbers found: {numbers}")
            return str(numbers[0])
        else:
            logger.error("No numbers found in the string")
            raise ValueError("No numbers found in the string")

    def answer_question_from_options(self, question: str, options: list[str]) -> str:
        logger.debug(f"Answering question from options: {question}")
        func_template = self._preprocess_template_string(prompts.options_template)
        prompt = ChatPromptTemplate.from_template(func_template)
        chain = prompt | self.llm_cheap | StrOutputParser()
        raw_output_str = chain.invoke(
            {
                RESUME: self.resume,
                JOB_APPLICATION_PROFILE: self.job_application_profile,
                QUESTION: question,
                OPTIONS: options,
            }
        )
        output_str = self._clean_llm_output(raw_output_str)
        logger.debug(f"Raw output for options question: {output_str}")
        best_option = self.find_best_match(output_str, options)
        logger.debug(f"Best option determined: {best_option}")
        return best_option

    def determine_resume_or_cover(self, phrase: str) -> str:
        logger.debug(
            f"Determining if phrase refers to resume or cover letter: {phrase}"
        )
        prompt = ChatPromptTemplate.from_template(
            prompts.resume_or_cover_letter_template
        )
        chain = prompt | self.llm_cheap | StrOutputParser()
        raw_response = chain.invoke({PHRASE: phrase})
        response = self._clean_llm_output(raw_response)
        logger.debug(f"Response for resume_or_cover: {response}")
        if "resume" in response:
            return "resume"
        elif "cover" in response:
            return "cover"
        else:
            return "resume"

    def is_work_preferences_match(self, job: Job, work_preferences: dict) -> bool:
        """
        Determine if candidate's work preferences match the job requirements.

        Args:
            job: Job object containing details about the position
            work_preferences: Dictionary of candidate's work preferences

        Returns:
            bool: True if work preferences match the job, False otherwise
        """
        logger.debug("Checking if work preferences match template")

        # Create proper JSON parser with the expected schema
        parser = JsonOutputParser(pydantic_object=WorkPreferenceMatch)

        # Get format instructions for the parser
        format_instructions = parser.get_format_instructions()

        # Update the prompt to include parser instructions
        prompt = ChatPromptTemplate.from_template(
            prompts.is_work_preferences_match_template + "\n{format_instructions}"
        )

        # Build the chain with the parser
        chain = prompt | self.llm_cheap | parser

        # Create a copy of work_preferences to avoid modifying the input
        combined_preferences = work_preferences.copy()
        combined_preferences.update(self.job_application_profile.work_preferences.__dict__)

        # Copy job object to avoid modifying the input , saving input tokens
        job_copy = deepcopy(job)
        job_copy.description = ""
        job_copy.summarize_job_description = ""

        try:
            # Execute the chain with the format instructions
            output = chain.invoke(
                {
                    WORK_PREFERENCES : combined_preferences,
                    JOB : job_copy,
                    "format_instructions": format_instructions
                }
            )

            logger.debug(f"Work preferences match output: {output}")

            work_preferences_match = WorkPreferenceMatch(**output)

            return work_preferences_match.match
        except Exception as e:
            logger.error(f"Error in work preferences matching: {e} {traceback.format_exc()} ")
            return True

    def is_job_suitable(self, work_preferences : dict) -> Tuple[bool, Optional[int], Optional[str]]:
        """
        Determines if the job is suitable based on a score and reasoning extracted from LLM output.

        Returns:
            Tuple[bool, Optional[int], Optional[str]]: A tuple containing:
                - A boolean indicating if the job is suitable.
                - The suitability score (if available).
                - The reasoning (if available).
        """
        logger.info("Checking if job is suitable")

        # Create the prompt and process it through the chain
        prompt = ChatPromptTemplate.from_template(prompts.is_relavant_position_template)
        chain = prompt | self.llm_cheap | StrOutputParser()

        # Invoke the chain with resume and job description
        raw_output = chain.invoke(
            {
                RESUME: self.resume,
                JOB_DESCRIPTION: self.job_description,
                WORK_PREFERENCES: work_preferences
            }
        )

        # Clean and process LLM output
        output = self._clean_llm_output(raw_output)
        logger.debug(f"Job suitability output: {output}")

        try:
            # Extract score and reasoning using regex
            score_match = re.search(r"Score:\s*(\d+)", output, re.IGNORECASE)
            reasoning_match = re.search(r"Reasoning:\s*(.+)", output, re.IGNORECASE | re.DOTALL)

            score = int(score_match.group(1)) if score_match else None
            reasoning = reasoning_match.group(1).strip() if reasoning_match else None
        except AttributeError:
            logger.warning(
                "Failed to extract score or reasoning from LLM. "
                "Proceeding with application, but job may or may not be suitable."
            )
            return True, None, None

        logger.info(f"Job suitability score: {score}")

        # Determine suitability based on the score
        is_suitable = score is not None and score >= JOB_SUITABILITY_SCORE

        if not is_suitable:
            logger.debug(f"Job is not suitable: {reasoning}")

        return is_suitable, score, reasoning
