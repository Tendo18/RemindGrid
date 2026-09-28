release: python manage.py migrate --noinput
web: gunicorn api.wsgi --log-file -
worker: celery -A api worker --beat --loglevel=info