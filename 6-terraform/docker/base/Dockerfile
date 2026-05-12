FROM astral/uv:python3.11-trixie

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

ARG SERVICE_DIR

COPY ./pyproject.toml ./pyproject.toml

RUN uv sync

COPY ${SERVICE_DIR}/ ./

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
