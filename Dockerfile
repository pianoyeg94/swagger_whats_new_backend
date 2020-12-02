FROM python:3.9.0-slim

WORKDIR /usr/src/app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install gcc compiler, make utility, 
# postgres and image processing dependencies + netcat for entrypoint scripts
RUN apt-get update \
    && apt-get install -y gcc make libpq-dev libjpeg-dev libpng-dev netcat

RUN pip install --upgrade pip
COPY ./requirements.txt /usr/src/app/requirements.txt
COPY ./requirements.dev.txt /usr/src/app/requirements.dev.txt
RUN pip install -r requirements.dev.txt

COPY ./app /usr/src/app/

ENTRYPOINT ["/usr/src/app/scripts/entrypoint.sh"]