from typing import List
from selenium.webdriver.remote.webelement import WebElement
from src.job_portals.application_form_elements import SelectQuestion
from src.job_portals.base_job_portal import BaseApplicationPage

class LeverEasyApplicationPage(BaseApplicationPage):
    def save(self) -> None:
        raise NotImplementedError

    def discard(self) -> None:
        raise NotImplementedError

    def click_submit_button(self) -> None:
        raise NotImplementedError

    def handle_errors(self) -> None:
        raise NotImplementedError

    def has_submit_button(self) -> bool:
        raise NotImplementedError

    def get_file_upload_elements(self):
        raise NotImplementedError

    def upload_file(self, element, file_path: str) -> None:
        raise NotImplementedError

    def get_form_sections(self):
        raise NotImplementedError

    def accept_terms_of_service(self, section) -> None:
        raise NotImplementedError

    def is_terms_of_service(self, section) -> bool:
        raise NotImplementedError

    def is_radio_question(self, section) -> bool:
        raise NotImplementedError

    def web_element_to_radio_question(self, section):
        raise NotImplementedError

    def select_radio_option(self, radio_question_web_element, answer: str) -> None:
        raise NotImplementedError

    def is_textbox_question(self, section) -> bool:
        raise NotImplementedError

    def web_element_to_textbox_question(self, section):
        raise NotImplementedError

    def fill_textbox_question(self, section, answer: str) -> None:
        raise NotImplementedError

    def is_date_question(self, section) -> bool:
        raise NotImplementedError

    def has_next_button(self) -> bool:
        raise NotImplementedError

    def click_next_button(self) -> None:
        raise NotImplementedError

    def has_errors(self) -> None:
        raise NotImplementedError

    def check_for_errors(self) -> None:
        raise NotImplementedError

    def get_input_elements(self) -> List[WebElement]:
        raise NotImplementedError

    def is_upload_field(self, element: WebElement) -> bool:
        raise NotImplementedError

    def get_upload_element_heading(self, element: WebElement) -> str:
        raise NotImplementedError

    def is_dropdown_question(self, section: WebElement) -> bool:
        raise NotImplementedError

    def web_element_to_dropdown_question(self, section: WebElement) -> SelectQuestion:
        raise NotImplementedError

    def select_dropdown_option(self, section: WebElement, answer: str) -> None:
        raise NotImplementedError

