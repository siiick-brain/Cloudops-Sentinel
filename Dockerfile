FROM python:3.12.16-slim-trixie

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /srv
# Pick up Debian security fixes published after the base image was built.
RUN apt-get update && apt-get upgrade -y --no-install-recommends && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    addgroup --system --gid 10001 sentinel && \
    adduser --system --uid 10001 --ingroup sentinel sentinel
COPY app ./app
COPY scripts/loadgen.py ./scripts/loadgen.py
USER 10001:10001
EXPOSE 8000 8001
CMD ["uvicorn", "app.api:app", "--host", "0.0.0.0", "--port", "8000"]

