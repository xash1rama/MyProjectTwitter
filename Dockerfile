FROM python:3.12
USER root
RUN mkdir /app

RUN apt-get update && apt-get install -y python3-dev supervisor nginx \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app
RUN pip install -r /app/requirements.txt

COPY . /app


WORKDIR /app

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.ini"]
ENTRYPOINT ["gunicorn", "app:app", "-b", "0.0.0.0:8000"]