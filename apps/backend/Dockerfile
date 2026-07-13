# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Install dependencies from pyproject (standard extras)
COPY pyproject.toml ./
RUN pip install --no-cache-dir .[standard]

# Copy the application code
COPY . .

# Ensure the package source is importable (src/ layout)
ENV PYTHONPATH=/app
WORKDIR /app/src

# Expose port 8000 to the outside world
EXPOSE 8000

# Command to run the application.
# The FastAPI app instance is named `app` in `services/main_api_server.py`.
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8000/api/v1/ops/health').status==200 else 1)" || exit 1

CMD ["uvicorn", "services.main_api_server:app", "--host", "0.0.0.0", "--port", "8000"]