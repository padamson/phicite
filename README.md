# Test-Driven Development with FastAPI and Docker

[![CI/CD](https://github.com/padamson/fastapi-tdd-docker/actions/workflows/main.yml/badge.svg)](https://github.com/padamson/fastapi-tdd-docker/actions/workflows/main.yml)

## If starting from scratch...to build, generate database migrations, test, and check (with [ruff](https://docs.astral.sh/ruff/)) locally:

```bash
docker compose up -d --build
docker compose exec web aerich init-db
docker compose exec web python -m pytest # --cov="."  --cov-report html
docker compose exec web ruff check . # or ruff check --fix .
```

## To build and run the production image locally:

```bash
docker build -f phicite/Dockerfile.prod -t web ./phicite
docker run --name phicite -e PORT=8765 -e DATABASE_URL=sqlite://sqlite.db -p 5003:8765 web:latest
```

Navigate to [http://localhost:5003/ping/](http://localhost:5003/ping/).

Bring down the container when done:

```bash
docker rm phicite -f
```

## Deploy to Heroku

```bash 
heroku login
heroku create # store app name in APP_NAME
heroku container:login
heroku addons:create heroku-postgresql:essential-0 --app ${APP_NAME}
```

## Run database migrations on Heroku

```bash
heroku login
heroku run -a ${APP_NAME} aerich upgrade
```

## Run tests on production server

```bash
cd phicite
poetry run python prod_testing.py
```

## To create database migrations after changes to models

```bash
docker compose exec web aerich migrate
```

## To reset the database

To delete the existing `web_dev` and `web_test` databases in your Docker PostgreSQL container, you can use the following commands:

```bash
# Connect to the database container
docker compose exec web-db psql -U postgres

# Inside the PostgreSQL prompt, run:
DROP DATABASE IF EXISTS web_dev;
DROP DATABASE IF EXISTS web_test;
```
