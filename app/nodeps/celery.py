import os
from celery import Celery


if os.path.exists(".env"):
    f = open(".env")
    for line in f.readlines():
        if "=" in line:
            line = line.replace("\n", "").replace("\r", "")
            (key, val) = line.split("=")
            os.environ[key] = val
    f.close()

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nodeps.settings')

app = Celery('nodeps')
# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')



# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

#app.conf.broker_url = "redis://127.0.0.1:{}/0".format(os.environ.get("REDIS_PORT", 6379))
#app.conf.beat_schedule_filename = "test"



# Optional configuration, see the application user guide.
app.conf.update(
    result_expires=3600,
)


@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')



if __name__ == '__main__':
    app.start()