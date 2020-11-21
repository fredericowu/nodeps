from celery import shared_task


@shared_task
def add(msg):
    print("This is the msg", msg)

