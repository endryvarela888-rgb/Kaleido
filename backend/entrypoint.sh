#!/bin/sh
set -e

echo "Esperando a que Postgres esté listo..."
until python manage.py migrate --check > /dev/null 2>&1 || python -c "
import psycopg2, os, sys
from urllib.parse import urlparse
url = urlparse(os.environ['DATABASE_URL'])
try:
    psycopg2.connect(dbname=url.path[1:], user=url.username, password=url.password, host=url.hostname, port=url.port)
except Exception:
    sys.exit(1)
"; do
  sleep 1
done

echo "Aplicando migraciones..."
python manage.py migrate --noinput

echo "Recolectando archivos estáticos..."
python manage.py collectstatic --noinput

echo "Arrancando Gunicorn..."
exec gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 2