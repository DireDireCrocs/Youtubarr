#!/bin/sh
set -e

echo "[youtubarr] running entrypoint…"

python manage.py collectstatic --noinput
python manage.py migrate --noinput

if [ "${DJANGO_SUPERUSER_CREATE:-0}" = "1" ]; then
  python manage.py shell -c "
from django.contrib.auth import get_user_model;
User = get_user_model();
import os;
if not User.objects.filter(username=os.environ['DJANGO_SUPERUSER_USERNAME']).exists():
    User.objects.create_superuser(
        os.environ['DJANGO_SUPERUSER_USERNAME'],
        os.environ['DJANGO_SUPERUSER_EMAIL'],
        os.environ['DJANGO_SUPERUSER_PASSWORD']
    )
  "
fi

exec "$@"
