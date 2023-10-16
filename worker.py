import os
import ssl
from celery import Celery

worker = Celery(
    'celery-worker',
    broker=os.environ.get('REDIS_URI'),
    backend=os.environ.get('REDIS_URI'),
    broker_use_ssl = {
        'ssl_cert_reqs': ssl.CERT_NONE
     },
    redis_backend_use_ssl = {
        'ssl_cert_reqs': ssl.CERT_NONE
     },
    include=['activity_tracker_v2'],
)

@worker.task(name='addTask')  # Named task
def add(x, y):
    print('Task Add started')
    s = x + y
    print('Task Add done')
    return s