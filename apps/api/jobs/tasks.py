from celery import shared_task
from .services import execute_verification

@shared_task(name="tagger.verify_document", ignore_result=True)
def verify_document(job_id):
    execute_verification(job_id)
