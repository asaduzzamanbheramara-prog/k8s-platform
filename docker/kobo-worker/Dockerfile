FROM python:3.11-slim

RUN pip install celery redis django

CMD ["celery","-A","kobo","worker","-l","info"]
