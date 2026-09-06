FROM python:3.12-slim
WORKDIR /srv
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
# Databáze žije na persistentním svazku (/data); sync se pouští uvnitř stroje.
ENV RADAR_DB=/data/radar.db
EXPOSE 8080
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
