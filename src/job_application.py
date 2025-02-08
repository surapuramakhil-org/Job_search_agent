from attr import asdict
from job import Job
import json


class JobApplication:

    def __init__(self, job: Job):
        self.job = job
        self.resume_path = ""
        self.cover_letter_path = ""
        # contains only question -> added when discovered
        self.empty_form = []
        # contains question and answer -> added when answered
        self.application_form = []

    def add_question_to_form(self, question: str):
        self.empty_form.append(question)

    def save_application_data(self, application_question: dict):
        self.application_form.append(application_question)

    def set_resume_path(self, resume_path: str):
        self.resume_path = resume_path

    def set_cover_letter_path(self, cv_path: str):
        self.cover_letter_path = cv_path

    def to_json(self):
        return json.dumps({
            'job': self.job.to_dict(),
            'resume_path': self.resume_path,
            'cover_letter_path': self.cover_letter_path,
            'empty_form': self.empty_form,
            'application_form': self.application_form
        })
