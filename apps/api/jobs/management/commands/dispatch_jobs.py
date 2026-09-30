import time
from django.core.management.base import BaseCommand
from jobs.services import dispatch_pending
from jobs.tasks import verify_document

class Command(BaseCommand):
    help = "Publish durable pending jobs; safe to restart after broker outages."
    def add_arguments(self, parser):
        parser.add_argument("--once", action="store_true")
    def handle(self, *args, **options):
        while True:
            count = dispatch_pending(lambda job_id: verify_document.delay(job_id))
            if options["once"]:
                self.stdout.write(f"Published {count} job(s)")
                return
            time.sleep(5)
