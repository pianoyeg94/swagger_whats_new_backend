FROM python:3.8.0-alpine

WORKDIR /usr/src/app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install gcc compiler, make utility, 
# postgres, argon, celery and image processing dependencies
RUN apk update \
    && apk add postgresql-dev gcc python3-dev musl-dev \
        libffi-dev zlib libjpeg-turbo-dev libpng-dev make

RUN pip install --upgrade pip
COPY ./requirements.txt /usr/src/app/requirements.txt
COPY ./requirements.dev.txt /usr/src/app/requirements.dev.txt
RUN pip install -r requirements.dev.txt

COPY ./app /usr/src/app/

ENTRYPOINT ["/usr/src/app/scripts/entrypoint.sh"]