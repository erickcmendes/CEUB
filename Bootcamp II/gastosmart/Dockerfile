FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src
COPY data/.gitkeep ./data/.gitkeep
COPY .streamlit ./.streamlit

# Expose Streamlit's default port
EXPOSE 8501

# Run Streamlit binding to all network interfaces inside the container
CMD ["streamlit", "run", "src/app_web.py", "--server.port", "8501", "--server.address", "0.0.0.0"]
