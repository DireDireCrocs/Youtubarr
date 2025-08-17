FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# OS deps for runtime + supervisord + nginx
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential ca-certificates curl supervisor nginx \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Python deps
COPY app/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# App code
COPY app/ ./

# Nginx + supervisor + entrypoint
COPY nginx.conf /etc/nginx/sites-enabled/default
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Collect static (safe if none)
RUN mkdir -p /app/data && python manage.py collectstatic --noinput || true

EXPOSE 80

ENTRYPOINT ["/entrypoint.sh"]
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
