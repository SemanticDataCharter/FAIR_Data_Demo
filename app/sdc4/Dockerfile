FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -g 1000 appuser && \
    useradd -u 1000 -g 1000 -m -s /bin/bash appuser

# Install Python dependencies
COPY app/sdc4/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy Django project
COPY app/sdc4/ /app/

# Copy SPARQL queries (baked into image, no volume mount needed)
COPY sparql/ /sparql/

# Copy startup script
COPY scripts/start.sh /app/scripts/start.sh
RUN chmod +x /app/scripts/start.sh

# Create directories and collect static files
RUN mkdir -p staticfiles mediafiles && \
    SECRET_KEY=build-placeholder python manage.py collectstatic --noinput && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

EXPOSE 8080

CMD ["/app/scripts/start.sh"]
