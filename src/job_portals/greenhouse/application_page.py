"""
Greenhouse Application Page using browser-use AI agent.

This module provides job application form handling for Greenhouse
using the browser-use AI agent for agentic automation.
"""

import asyncio
import time
import traceback
from typing import List, Optional, Any

from browser_use import Agent, Browser
from browser_use.browser.profile import BrowserProfile
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from custom_exception import JobSkipException
from job_portals.application_form_elements import (
    SelectQuestion,
    SelectQuestionType,
    TextBoxQuestion,
    TextBoxQuestionType,
)
from job_portals.base_job_portal import BaseApplicationPage
from logger import logger
from utils import browser_utils


class GreenhouseApplicationPage(BaseApplicationPage):
    """
    Greenhouse application page using browser-use AI agent.

    Handles job application forms using AI-powered browser automation
    with fallback to Selenium for reliability.
    """

    def __init__(self, driver):
        """
        Initialize the Greenhouse application page.

        Args:
            driver: Selenium WebDriver instance.
        """
        super().__init__(driver)
        self._browser: Optional[Browser] = None
        self._llm = None
        self._job_application_profile = None

    def set_llm(self, llm):
        """Set the LLM for the browser agent."""
        self._llm = llm

    def set_job_application_profile(self, profile):
        """Set the job application profile."""
        self._job_application_profile = profile

    async def _get_browser(self) -> Browser:
        """Get or create browser instance."""
        if self._browser is None:
            profile = BrowserProfile(headless=False)
            self._browser = Browser(browser_profile=profile)
        return self._browser

    def has_save_button(self) -> bool:
        return False

    def save(self) -> None:
        raise NotImplementedError

    def discard(self) -> None:
        raise NotImplementedError

    def application_submission_confirmation(self) -> bool:
        """Check if application was submitted successfully."""
        try:
            confirmation = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        "//*[contains(normalize-space(), 'Application submitted') or "
                        "contains(normalize-space(), 'Thank you') or "
                        "contains(normalize-space(), 'application has been received')]",
                    )
                )
            )
            return confirmation.is_displayed()
        except (NoSuchElementException, TimeoutException):
            return False
        except Exception as e:
            logger.error(f"Confirmation check error: {e}")
            return False

    def wait_until_ready(self):
        """Wait for the page to be ready."""
        try:
            WebDriverWait(self.driver, 120).until(
                EC.invisibility_of_element_located(
                    (By.XPATH, "//div[contains(@class, 'loading')]")
                )
            )
        except TimeoutException as e:
            logger.error(f"Loading timeout: {str(e)}")
            raise JobSkipException("Page load timeout")
        except Exception as e:
            logger.error(f"Error waiting for page: {e}")
            raise

    def click_submit_button(self) -> None:
        """Click the submit button."""
        try:
            selectors = [
                (By.ID, "submit_app"),
                (By.XPATH, "//button[@type='submit']"),
                (By.XPATH, "//button[contains(text(), 'Submit')]"),
                (By.XPATH, "//input[@type='submit']"),
            ]

            for by, selector in selectors:
                try:
                    btn = self.driver.find_element(by, selector)
                    if btn.is_displayed() and btn.is_enabled():
                        btn.click()
                        return
                except Exception:
                    continue

            raise Exception("Submit button not found")

        except Exception as e:
            logger.error(f"Error clicking submit: {e}")
            browser_utils.security_check(self.driver)

    def handle_errors(self) -> None:
        raise NotImplementedError

    def has_submit_button(self) -> bool:
        """Check if submit button exists."""
        selectors = [
            (By.ID, "submit_app"),
            (By.XPATH, "//button[@type='submit']"),
            (By.XPATH, "//button[contains(text(), 'Submit')]"),
        ]

        for by, selector in selectors:
            try:
                elem = self.driver.find_element(by, selector)
                if elem.is_displayed():
                    return True
            except Exception:
                continue

        return False

    def get_file_upload_elements(self):
        raise NotImplementedError

    def upload_file(self, element: WebElement, file_path: str) -> None:
        """Upload a file to the given element."""
        try:
            file_input = element.find_element(By.XPATH, ".//input[@type='file']")
            file_input.send_keys(file_path)
        except Exception as e:
            logger.error(f"Error uploading file: {e}")
            raise

    def get_form_sections(self) -> List[WebElement]:
        """Get form sections from the application page."""
        try:
            selectors = [
                "//div[contains(@class, 'field')]",
                "//fieldset",
                "//form//div[contains(@class, 'section')]",
            ]

            for selector in selectors:
                try:
                    sections = self.driver.find_elements(By.XPATH, selector)
                    if sections:
                        return sections
                except Exception:
                    continue

            # Fallback to form itself
            try:
                form = self.driver.find_element(By.ID, "application")
                return [form]
            except Exception:
                return []

        except Exception as e:
            logger.error(f"Error getting form sections: {e}")
            return []

    def accept_terms_of_service(self, element: WebElement) -> None:
        """Accept terms of service checkbox."""
        try:
            checkbox = element.find_element(By.XPATH, ".//input[@type='checkbox']")
            if not checkbox.is_selected():
                self.driver.execute_script("arguments[0].click();", checkbox)
        except Exception as e:
            logger.error(f"Terms acceptance error: {e}")
            raise

    def is_terms_of_service(self, element: WebElement) -> bool:
        """Check if element is a terms of service checkbox."""
        try:
            checkbox = element.find_element(By.XPATH, ".//input[@type='checkbox']")
            label_text = element.text.lower()
            keywords = ["consent", "agree", "terms", "privacy", "acknowledge"]
            return any(kw in label_text for kw in keywords)
        except NoSuchElementException:
            return False

    def is_radio_question(self, element: WebElement) -> bool:
        """Check if element is a radio/checkbox question."""
        try:
            element.find_element(
                By.XPATH, ".//input[@type='checkbox' or @type='radio']"
            )
            return not self.is_terms_of_service(element)
        except NoSuchElementException:
            return False

    def web_element_to_radio_question(self, element: WebElement) -> SelectQuestion:
        """Convert element to SelectQuestion."""
        try:
            # Get question label
            label = ""
            try:
                label_elem = element.find_element(By.XPATH, ".//label")
                label = label_elem.text.strip()
            except Exception:
                label = element.text.strip()

            # Get options
            inputs = element.find_elements(
                By.XPATH, ".//input[@type='radio' or @type='checkbox']"
            )
            options = []
            for inp in inputs:
                try:
                    inp_id = inp.get_attribute("id")
                    if inp_id:
                        opt_label = element.find_element(
                            By.XPATH, f".//label[@for='{inp_id}']"
                        )
                        opt_text = opt_label.text.strip()
                        if opt_text and opt_text not in options:
                            options.append(opt_text)
                    else:
                        val = inp.get_attribute("value")
                        if val and val not in options:
                            options.append(val)
                except Exception:
                    val = inp.get_attribute("value")
                    if val and val not in options:
                        options.append(val)

            # Determine type
            q_type = SelectQuestionType.SINGLE_SELECT
            if any(inp.get_attribute("type") == "checkbox" for inp in inputs):
                q_type = SelectQuestionType.MULTI_SELECT

            return SelectQuestion(
                question=label,
                options=options,
                type=q_type,
                required=False,
            )
        except Exception as e:
            logger.error(f"Error converting to radio question: {e}")
            raise

    def select_radio_option(
        self, radio_question_web_element: WebElement, answer: str
    ) -> None:
        """Select a radio option."""
        try:
            # Try by label
            try:
                label = radio_question_web_element.find_element(
                    By.XPATH, f".//label[normalize-space(text())='{answer}']"
                )
                input_id = label.get_attribute("for")
                if input_id:
                    radio = radio_question_web_element.find_element(By.ID, input_id)
                    radio.click()
                    return
            except Exception:
                pass

            # Try by value
            radio = radio_question_web_element.find_element(
                By.XPATH, f".//input[@value='{answer}']"
            )
            radio.click()
        except Exception as e:
            logger.error(f"Error selecting radio option: {e}")
            raise

    def is_textbox_question(self, element: WebElement) -> bool:
        """Check if element is a textbox question."""
        try:
            if element.find_elements(By.XPATH, ".//textarea"):
                return True
            inp = element.find_element(
                By.XPATH, ".//input[@type='text' or @type='number' or @type='email']"
            )
            return inp.is_displayed() and inp.is_enabled()
        except NoSuchElementException:
            return False

    def web_element_to_textbox_question(self, element: WebElement) -> TextBoxQuestion:
        """Convert element to TextBoxQuestion."""
        try:
            # Get label
            label = ""
            try:
                label_elem = element.find_element(By.XPATH, ".//label")
                label = label_elem.text.strip()
            except Exception:
                label = element.text.strip()

            # Get input element
            inp = element.find_element(
                By.XPATH,
                ".//input[@type='text' or @type='number' or @type='email'] | .//textarea",
            )

            # Determine type
            inp_type = inp.tag_name if inp.tag_name == "textarea" else inp.get_attribute("type")
            if inp_type in ("text", "textarea"):
                q_type = TextBoxQuestionType.TEXT
            elif inp_type == "number":
                q_type = TextBoxQuestionType.NUMERIC
            elif inp_type == "email":
                q_type = TextBoxQuestionType.EMAIL
            else:
                q_type = TextBoxQuestionType.TEXT

            return TextBoxQuestion(
                question=label,
                type=q_type,
                required=False,
            )
        except Exception as e:
            logger.error(f"Error converting to textbox question: {e}")
            raise

    def fill_textbox_question(self, element: WebElement, answer: str) -> None:
        """Fill a textbox with the given answer."""
        try:
            inp = element.find_element(
                By.XPATH,
                ".//textarea | .//input[@type='text' or @type='number' or @type='email']",
            )
            inp.clear()
            inp.send_keys(answer)
        except Exception as e:
            logger.error(f"Error filling textbox: {e}")
            raise

    def is_date_question(self, element: WebElement) -> bool:
        """Check if element is a date question."""
        try:
            element.find_element(By.XPATH, ".//input[@type='date']")
            return True
        except NoSuchElementException:
            return False

    def has_next_button(self) -> bool:
        """Check if there's a next button."""
        selectors = [
            (By.XPATH, "//button[contains(text(), 'Next')]"),
            (By.XPATH, "//button[contains(text(), 'Continue')]"),
        ]
        for by, selector in selectors:
            try:
                elem = self.driver.find_element(by, selector)
                if elem.is_displayed():
                    return True
            except Exception:
                continue
        return False

    def click_next_button(self) -> None:
        """Click the next button."""
        selectors = [
            (By.XPATH, "//button[contains(text(), 'Next')]"),
            (By.XPATH, "//button[contains(text(), 'Continue')]"),
        ]
        for by, selector in selectors:
            try:
                btn = self.driver.find_element(by, selector)
                if btn.is_displayed():
                    btn.click()
                    return
            except Exception:
                continue
        raise Exception("Next button not found")

    def has_errors(self) -> None:
        raise NotImplementedError

    def check_for_errors(self) -> None:
        raise NotImplementedError

    def get_input_elements(self, form_section: WebElement) -> List[WebElement]:
        """Get input elements from a form section."""
        try:
            elements = form_section.find_elements(
                By.XPATH, ".//div[contains(@class, 'field')]"
            )
            if not elements:
                elements = form_section.find_elements(
                    By.XPATH, ".//textarea | .//input | .//select"
                )
            return elements
        except Exception as e:
            logger.error(f"Error getting input elements: {e}")
            return []

    def is_upload_field(self, element: WebElement) -> bool:
        """Check if element is a file upload field."""
        try:
            element.find_element(By.XPATH, ".//input[@type='file']")
            return True
        except NoSuchElementException:
            return False

    def get_upload_element_heading(self, element: WebElement) -> str:
        """Get the heading/label for an upload field."""
        try:
            label = element.find_element(By.XPATH, ".//label")
            return label.text
        except Exception:
            return element.text

    def is_dropdown_question(self, element: WebElement) -> bool:
        """Check if element is a dropdown question."""
        try:
            element.find_element(By.XPATH, ".//select")
            return True
        except NoSuchElementException:
            return False

    def web_element_to_dropdown_question(self, element: WebElement) -> SelectQuestion:
        """Convert element to SelectQuestion for dropdown."""
        try:
            # Get label
            label = ""
            try:
                label_elem = element.find_element(By.XPATH, ".//label")
                label = label_elem.text.strip()
            except Exception:
                label = element.text.strip()

            # Get select options
            select_elem = element.find_element(By.XPATH, ".//select")
            options = [
                opt.text
                for opt in select_elem.find_elements(By.TAG_NAME, "option")
                if opt.text.strip()
            ]

            # Determine type
            is_multi = select_elem.get_attribute("multiple")
            q_type = (
                SelectQuestionType.MULTI_SELECT if is_multi
                else SelectQuestionType.SINGLE_SELECT
            )

            return SelectQuestion(
                question=label,
                options=options,
                type=q_type,
                required=False,
            )
        except Exception as e:
            logger.error(f"Error converting to dropdown question: {e}")
            raise

    def select_dropdown_option(self, element: WebElement, answer: str) -> None:
        """Select a dropdown option."""
        try:
            select_elem = element.find_element(By.XPATH, ".//select")
            for option in select_elem.find_elements(By.TAG_NAME, "option"):
                if option.text == answer:
                    option.click()
                    return
            raise ValueError(f"Option '{answer}' not found")
        except Exception as e:
            logger.error(f"Error selecting dropdown option: {e}")
            raise

    async def close(self):
        """Close browser resources."""
        if self._browser:
            await self._browser.stop()
            self._browser = None
