FROM python:3.11-slim AS telegram

ENV LANG=en_US.UTF-8 \
    LANGUAGE=en_US:en \
    LC_ALL=en_US.UTF-8

WORKDIR /app

COPY . .

RUN pip install -r requirements.txt
CMD ["python3", "main.py"]
