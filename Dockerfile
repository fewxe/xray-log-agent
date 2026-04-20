FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir uv
COPY pyproject.toml .

RUN uv sync

COPY . /app

RUN mkdir -p /var/log/xray

EXPOSE 8080

CMD ["uv", "run", "faststream", "run", "app.main:app"]
