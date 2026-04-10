FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install build prerequisites for pandas/numpy
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential git \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
COPY __init__.py ./
COPY client/ ./client/
RUN pip install --upgrade pip \
    && pip install ".[client]"

EXPOSE 8501

CMD ["streamlit", "run", "client/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
