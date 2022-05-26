# FROM revolutionsystems/python:3.6.3-wee-optimized-lto as python-base
# FROM revolutionsystems/python:3.6.3-wee-optimized-lto
FROM python:3.6.4
ENV PYTHONUNBUFFERED 1
# RUN apt-get update && apt-get install -y git build-essential
RUN pip install -U pip==19.0

COPY requirements /requirements
RUN pip install -U pip==19.0

RUN pip install -r /requirements/production.txt
#COPY registration_service/ /registration_service
RUN echo 'hello'
RUN pip install -e git+https://gbozee:abiola2321@gitlab.com/careerlyft-team/careerlyft-shared.git@master#egg=cv_utils
COPY . /registration_service

# FROM python:3.6-alpine
# COPY --from=python-base /root/.cache /root/.cache
# COPY --from=python-base /registration_service /registration_service
# RUN pip install -r /registration_service/requirements/production.txt && rm -rf /root/.cache
RUN find . | grep -E "(__pycache__|\.pyc|\.pyo$)" | xargs rm -rf
EXPOSE 5000

WORKDIR /registration_service
ENV DJANGO_SETTINGS_MODULE registration_service.settings.production

# CMD uvicorn --host=0.0.0.0 --port=5000 run:app
CMD gunicorn --workers=4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:5000 run:app --access-logfile -
