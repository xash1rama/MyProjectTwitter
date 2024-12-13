FROM python:3.12

RUN mkdir /app && apt-get update && apt-get install -y python3-dev supervisor nginx netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app
RUN pip install -r /app/requirements.txt

COPY . /app
COPY static /usr/share/nginx/html/static
COPY nginx.conf /etc/nginx/nginx.conf
COPY uwsgi.ini /etc/uwsgi/uwsgi.ini
EXPOSE 5050
WORKDIR /app
CMD ["uvicorn", "app:app", "--proxy-headers", "--host", "0.0.0.0", "--port", "5050", "--reload"]
