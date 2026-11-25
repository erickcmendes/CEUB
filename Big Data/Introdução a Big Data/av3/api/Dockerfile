FROM python:3.11-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1 CASS_DRIVER_NO_CYTHON=1
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY main.py .
# alert_rules.py (regras compartilhadas com os jobs Spark) é montado em /app/shared
ENV PYTHONPATH=/app/shared
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
