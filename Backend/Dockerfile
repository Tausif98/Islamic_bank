FROM python:3.12-slim

# Prevents Python from writing .pyc files and enables log streaming
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies first (layer cached unless requirements.txt changes)
# ✅ Fix — system deps first, then pip (better layer caching)
RUN apt-get update && apt-get install -y --no-install-recommends \
    dnsutils curl \          
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Expose FastAPI port
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
    #  "--host", "0.0.0.0", \
    #  "--port", "8000", \
    #  "--workers", "4", \
    #  "--timeout-keep-alive", "65", \
    #  "--limit-max-requests", "1000", \
    #  "--log-level", "info", \
    #  "--proxy-headers", \
    #  "--forwarded-allow-ips", "*"]

# Production: gunicorn manages multiple uvicorn workers
# --workers = number of CPU cores × 2 + 1 (rule of thumb)
# CMD ["gunicorn", "app.main:app", \
#      "--worker-class", "uvicorn.workers.UvicornWorker", \
#      "--workers", "4", \
#      "--bind", "0.0.0.0:8000", \
#      "--timeout", "120", \
#      "--access-logfile", "-"]