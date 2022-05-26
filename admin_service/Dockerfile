# FROM revolutionsystems/python:3.6.3-wee-optimized-lto as python-base
# FROM revolutionsystems/python:3.6.3-wee-optimized-lto
FROM python:3.6.4

ENV PYTHONUNBUFFERED 1
# RUN apt-get update && apt-get install -y git build-essential


COPY requirements /requirements
RUN pip install -U pip==19.0
RUN pip install -r /requirements/production.txt
COPY . /admin_service

RUN find . | grep -E "(__pycache__|\.pyc|\.pyo$)" | xargs rm -rf

EXPOSE 5000

WORKDIR /admin_service
ENV DJANGO_SETTINGS_MODULE admin_service.settings.production

RUN mkdir /var/django-static

CMD gunicorn --workers=4 -b 0.0.0.0:5000 admin_service.wsgi:application --access-logfile -
# CMD gunicorn --workers=4 --worker-class="egg:meinheld#gunicorn_worker" -b 0.0.0.0:5000 admin_service.wsgi:application --access-logfile -
