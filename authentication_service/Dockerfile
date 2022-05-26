# FROM revolutionsystems/python:3.6.3-wee-optimized-lto as python-base
# FROM revolutionsystems/python:3.6.3-wee-optimized-lto
FROM python:3.6.4

ENV PYTHONUNBUFFERED 1
# RUN apt-get update && apt-get install -y git build-essential
RUN pip install -U pip==19.0

COPY requirements /requirements
RUN pip install -U pip==19.0

RUN pip install -e git+https://gbozee:abiola2321@gitlab.com/careerlyft-team/careerlyft-shared.git#egg=cv_utils
RUN pip install -r /requirements/production.txt
COPY . /authentication_service
#COPY authentication_service/ /authentication_service

# FROM python:3.6-alpine
# COPY --from=python-base /root/.cache /root/.cache
# COPY --from=python-base /authentication_service /authentication_service
# RUN pip install -r /authentication_service/requirements/production.txt && rm -rf /root/.cache
RUN find . | grep -E "(__pycache__|\.pyc|\.pyo$)" | xargs rm -rf
EXPOSE 5000

WORKDIR /authentication_service
ENV DJANGO_SETTINGS_MODULE authentication_service.settings.production

CMD gunicorn --workers=4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:5000 run:app --access-logfile -
