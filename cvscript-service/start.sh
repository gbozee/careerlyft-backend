gunicorn --workers=2 django_app.wsgi:application
# gunicorn --workers=2 --worker-class="egg:meinheld#gunicorn_worker" django_app.wsgi:application