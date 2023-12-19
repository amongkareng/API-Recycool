FROM python:3.9-slim

ENV PYTHONBUFFERED True

WORKDIR /app

COPY . ./

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8080

CMD exec gunicorn -b 0.0.0.0:8080 --workers 1 --threads 8 --timeout 0 app:app