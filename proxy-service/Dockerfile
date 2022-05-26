# FROM revolutionsystems/python:3.6.3-wee-optimized-lto as python-base
FROM python:3.6.4

ENV PYTHONUNBUFFERED 1
# RUN apt-get update && apt-get install -y git build-essential
RUN pip install -U pip==19.0

RUN pip install -U pip==19.0
RUN pip install aiohttp django
RUN pip install gunicorn
RUN pip install -e git+https://gbozee:abiola2321@gitlab.com/careerlyft-team/careerlyft-shared.git#egg=cv_utils
COPY . /proxy-service

# FROM python:3.6-alpine
# COPY --from=python-base /root/.cache /root/.cache
# COPY --from=python-base /authentication_service /authentication_service
# RUN pip install -r /authentication_service/requirements/production.txt && rm -rf /root/.cache
RUN find . | grep -E "(__pycache__|\.pyc|\.pyo$)" | xargs rm -rf
EXPOSE 5000

WORKDIR /proxy-service

CMD gunicorn --workers=4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:5000 run:app --access-logfile -
