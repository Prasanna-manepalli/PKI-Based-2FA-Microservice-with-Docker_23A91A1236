# ---------- Stage 1: Builder ----------
FROM python:3.11-slim AS builder

WORKDIR /app

COPY requirements.txt .
RUN python -m pip install --upgrade pip \
    && pip install --prefix=/install -r requirements.txt

COPY main.py .
COPY student_private.pem student_public.pem instructor_public.pem .

# ---------- Stage 2: Runtime ----------
FROM python:3.11-slim

ENV TZ=UTC

WORKDIR /srv/app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y cron tzdata \
    && rm -rf /var/lib/apt/lists/*

# Set timezone to UTC
RUN ln -sf /usr/share/zoneinfo/UTC /etc/localtime

# Copy Python deps
COPY --from=builder /install /usr/local

# Copy application code
COPY --from=builder /app/main.py .
COPY --from=builder /app/student_private.pem .
COPY --from=builder /app/student_public.pem .
COPY --from=builder /app/instructor_public.pem .

# Create volume directories
RUN mkdir -p /data /cron && chmod 755 /data /cron

EXPOSE 8080

# Start API server (cron will be added in Step 10)
# Copy cron files
COPY cron/2fa-cron /etc/cron.d/2fa-cron
COPY scripts/log_2fa_cron.py /srv/app/scripts/log_2fa_cron.py

# Set permissions for cron
RUN chmod 0644 /etc/cron.d/2fa-cron \
    && chmod +x /srv/app/scripts/log_2fa_cron.py \
    && crontab /etc/cron.d/2fa-cron

# Start cron and API
CMD cron && uvicorn main:app --host 0.0.0.0 --port 8080

