FROM python:3.6-alpine
COPY api /app
WORKDIR /app
RUN pip install gunicorn Flask
CMD ["gunicorn", "-w 4", "flask_app:app"]
