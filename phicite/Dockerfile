# pull official base image
FROM python:3.13-alpine@sha256:452682e4648deafe431ad2f2391d726d7c52f0ff291be8bd4074b10379bb89ff

# set working directory
WORKDIR /usr/src/app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# install system dependencies
RUN apk update \
  && apk add netcat-openbsd gcc postgresql \
  && apk del

# install python dependencies
RUN pip install --upgrade pip
COPY ./requirements.txt .
COPY ./requirements-dev.txt .
RUN pip install -r requirements-dev.txt

# add app
COPY . .

# add entrypoint.sh
COPY ./entrypoint.sh .
RUN chmod +x /usr/src/app/entrypoint.sh

# run entrypoint.sh
ENTRYPOINT ["/usr/src/app/entrypoint.sh"]