FROM python:3.8
USER root
RUN mkdir /app

COPY requirements.txt /app

RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip
RUN pip install -r /app/requirements.txt

COPY . /app

WORKDIR /app

ENTRYPOINT ["gunicorn", "main:app", "-b", "0.0.0.0:8000"]