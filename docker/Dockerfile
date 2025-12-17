FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    PORT=8000

# system deps (adjust if you need extra libs for pandas/numpy)
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        gcc \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# copy dependency list early for layer caching
COPY requirements.txt /app/requirements.txt

RUN pip install --upgrade pip setuptools wheel \
 && pip install -r /app/requirements.txt

# copy source
COPY . /app

# create non-root user
RUN useradd --create-home appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE ${PORT}

# default command: use gunicorn for production (adjust module path if needed)
CMD ["sh", "-c", "gunicorn -w 4 -b 0.0.0.0:${PORT} 'hsim.GSOM.flask.app:app'"]
