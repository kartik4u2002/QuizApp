from celery import Celery
import os

redis_url = os.environ.get("REDIS_URL", "redis://redis:6379/0")

celery_app = Celery(
    "nlp_quiz_worker",
    broker=redis_url,
    backend=redis_url,
    include=['worker.tasks']
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)

# Schedule for periodic news ingestion
celery_app.conf.beat_schedule = {
    'fetch-news-every-5-minutes': {
        'task': 'worker.tasks.fetch_and_process_news',
        'schedule': 300.0, # 300 seconds = 5 minutes
    },
}
