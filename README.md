# Test-Driven Development with FastAPI and Docker

[![CI/CD](https://github.com/padamson/fastapi-tdd-docker/actions/workflows/main.yml/badge.svg)](https://github.com/padamson/fastapi-tdd-docker/actions/workflows/main.yml)

## To build, test, and check (with [ruff](https://docs.astral.sh/ruff/)) locally:

```bash
$ docker compose down -v # if needed
$ docker compose up -d --build
$ docker compose exec web aerich upgrade
$ docker compose exec web python -m pytest # --cov="."  --cov-report html
$ docker compose exec web ruff check . # or ruff check --fix .
```

## To build and run the production image locally:

```bash
$ docker build -f phicite/Dockerfile.prod -t web ./phicite
$ docker run --name phicite -e PORT=8765 -e DATABASE_URL=sqlite://sqlite.db -p 5003:8765 web:latest
```

Navigate to [http://localhost:5003/ping/](http://localhost:5003/ping/).

Bring down the container when done:
```bash
$ docker rm phicite -f
```
