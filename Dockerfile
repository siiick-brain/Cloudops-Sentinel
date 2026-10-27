FROM python:3.12.10-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /srv
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    addgroup --system --gid 10001 sentinel && \
    adduser --system --uid 10001 --ingroup sentinel sentinel
COPY app ./app
COPY scripts/loadgen.py ./scripts/loadgen.py
USER 10001:10001
EXPOSE 8000 8001
CMD ["uvicorn", "app.api:app", "--host", "0.0.0.0", "--port", "8000"]

