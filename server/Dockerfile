# Penciled API image. Build from the REPO ROOT (the image needs shared/python):
#   docker build -f server/Dockerfile -t penciled-api .
# No secrets are baked in: DATABASE_URL (and later the provider key) come from the
# host secret store at runtime. One process, one worker (idempotency results are
# in process memory). uvicorn's access log is off; no request body is ever logged.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PORT=8080

WORKDIR /srv
COPY shared/python /srv/shared/python
COPY server/pyproject.toml server/alembic.ini /srv/server/
COPY server/app /srv/server/app
RUN pip install /srv/shared/python /srv/server \
    && useradd --system --uid 10001 --no-create-home --shell /usr/sbin/nologin penciled

USER 10001
WORKDIR /srv/server
EXPOSE 8080
# Migrations run separately (fly.toml release_command / a Cloud Run job): alembic upgrade head
CMD ["python", "-m", "app.serve"]
