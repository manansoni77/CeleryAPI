import ssl
from celery import Celery

app = Celery(
    'celery-worker',
    broker='rediss://red-cklp56rj89us7381j49g:u4zZSfn7Zsc8Ak99xRYEgoT9CXbky75E@singapore-redis.render.com:6379',
    backend='rediss://red-cklp56rj89us7381j49g:u4zZSfn7Zsc8Ak99xRYEgoT9CXbky75E@singapore-redis.render.com:6379',
    broker_use_ssl = {
        'ssl_cert_reqs': ssl.CERT_NONE
     },
    redis_backend_use_ssl = {
        'ssl_cert_reqs': ssl.CERT_NONE
     },
    include=['activity_tracker_v2'],
)

@app.task(name='addTask')  # Named task
def add(x, y):
    print('Task Add started')
    s = x + y
    print('Task Add done')
    return s