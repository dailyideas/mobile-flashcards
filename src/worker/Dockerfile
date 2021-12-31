# syntax=docker/dockerfile:1
FROM python:3.8-slim

## Ref: https://stackoverflow.com/questions/59732335/is-there-any-disadvantage-in-using-pythondontwritebytecode-in-docker
ENV PYTHONDONTWRITEBYTECODE 1 
ENV PYTHONUNBUFFERED 1

## Ref: https://serverfault.com/questions/683605/docker-container-time-timezone-will-not-reflect-changes
ARG APP_TIMEZONE
RUN ln -snf /usr/share/zoneinfo/${APP_TIMEZONE} /etc/localtime && echo ${APP_TIMEZONE} > /etc/timezone

RUN apt-get update && \
    apt-get install -y --no-install-recommends cron nano

WORKDIR /usr/app

COPY ./requirements.txt ./
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip && \
    pip install --no-cache-dir -r ./requirements.txt

COPY ./ ./

## Capture SIGTERM in python script
## 
## Reference
## ---- ----
## 1. https://stackoverflow.com/questions/64954213/python-how-to-recieve-sigint-in-docker-to-stop-service
# CMD ["./startup.sh"]
ENTRYPOINT ["python", "main.py"]
