FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN groupadd --system app && useradd --system --gid app --create-home app

COPY --chown=app:app pyproject.toml README.md ./
COPY --chown=app:app app ./app

RUN pip install --no-cache-dir .

RUN mkdir -p /app/data && chown -R app:app /app

USER app

EXPOSE 8000

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
