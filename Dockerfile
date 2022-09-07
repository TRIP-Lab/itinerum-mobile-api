FROM alpine:3.7
MAINTAINER Kyle Fitzsimmons "kfitzsimmons@gmail.com"
RUN apk add python python-dev musl-dev gcc py-pip libpq postgresql-dev git openssh py-virtualenv --no-cache
RUN pip install --upgrade pip
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
ENTRYPOINT exec gunicorn wsgi_mobile:app -b 0.0.0.0:$IT_MOBILE_PORT -k gevent -w 2 --access-logfile=- --timeout=45
