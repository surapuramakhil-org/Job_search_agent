from src.job_portals.base_job_portal import BaseJobPage

class LeverEasyApplyJobPage(BaseJobPage):
    def goto_job_page(self, job):
        raise NotImplementedError

    def get_apply_button(self, job_context):
        raise NotImplementedError

    def check_for_premium_redirect(self, job, max_attempts=3):
        raise NotImplementedError

    def click_apply_button(self, job_context) -> None:
        raise NotImplementedError

    def get_easy_apply_button(self, job_context):
        raise NotImplementedError

    def _find_easy_apply_button(self, job_context):
        raise NotImplementedError

    def _scroll_page(self) -> None:
        raise NotImplementedError

    def get_job_description(self, job) -> str:
        raise NotImplementedError

    def get_recruiter_link(self) -> str:
        raise NotImplementedError
