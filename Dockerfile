# Use slim Python image
FROM python:3.10-slim

# Prevent Python from writing pyc files
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# System dependencies (Postgres, Pillow, etc.)
RUN apt-get update \
    && apt-get install -y gcc libpq-dev \
    && apt-get clean

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy project
COPY . .

# Expose port
EXPOSE 8000

# Run Gunicorn (production server)
CMD ["gunicorn", "backend.wsgi:application", "--bind", "0.0.0.0:8000"]
