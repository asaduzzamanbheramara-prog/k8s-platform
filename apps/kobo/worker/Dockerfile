FROM python:3.11-slim

WORKDIR /srv/src

COPY . /srv/src/

ENV PYTHONPATH=/srv/src
ENV DJANGO_SETTINGS_MODULE=kobo.settings

RUN pip install celery redis django

CMD ["celery", "-A", "apps.kobo.celery", "worker", "-l", "info", "--concurrency=2"]
