FROM python:3.12

RUN mkdir /app && apt-get update && apt-get install -y python3-dev supervisor nginx \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app
RUN pip install -r /app/requirements.txt

COPY .flake8 /app
COPY app.py /app
COPY database /app/database
COPY schemas /app/schemas/
COPY static /app/static/
COPY static /usr/share/nginx/html/static
COPY mypy.ini /app
COPY nginx.conf /etc/nginx/nginx.conf
COPY uwsgi.ini /etc/uwsgi/uwsgi.ini
COPY supervisord.ini /etc/supervisor/conf.d/supervisord.ini

WORKDIR /app

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.ini"]

