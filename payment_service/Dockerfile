# FROM revolutionsystems/python:3.6.3-wee-optimized-lto as python-base
# FROM revolutionsystems/python:3.6.3-wee-optimized-lto
FROM python:3.6.4

# FROM python:3.7.0
ENV PYTHONUNBUFFERED 1
# RUN apt-get update && apt-get install -y git build-essential
RUN pip install -U pip==19.0

COPY requirements /requirements

RUN pip install -r /requirements/production.txt
RUN pip install -e git+https://gbozee:abiola2321@gitlab.com/careerlyft-team/careerlyft-shared.git#egg=cv_utils

COPY . /payment_service

RUN find . | grep -E "(__pycache__|\.pyc|\.pyo$)" | xargs rm -rf

EXPOSE 5000

WORKDIR /payment_service
ENV DJANGO_SETTINGS_MODULE payment_service.settings.production

CMD gunicorn --workers=4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:5000 run:app --access-logfile -