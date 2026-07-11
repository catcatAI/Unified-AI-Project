# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Install dependencies from pyproject (standard extras)
COPY pyproject.toml ./
RUN pip install --no-cache-dir .[standard]

# Copy the application code
COPY . .

# Expose port 8000 to the outside world
EXPOSE 8000

# Command to run the application
# Assumes the FastAPI app instance is named 'app' in 'main.py'
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]