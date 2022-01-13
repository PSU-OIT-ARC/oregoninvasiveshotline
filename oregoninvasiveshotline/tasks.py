from django.core.management import call_command

from oregoninvasiveshotline.celery import app


@app.task
def clear_expired_sessions():
    call_command('clearsessions')
