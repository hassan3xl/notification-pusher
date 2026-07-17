# Use a stable Python 3.12 slim image
FROM python:3.12-slim-bookworm

# Prevent Python from writing .pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies (netcat for wait check)
RUN apt-get update && apt-get install -y --no-install-recommends \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# Install uv for package management
RUN pip install uv

# Install Python dependencies
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# Copy the rest of the code
COPY . .

# Make entrypoint.sh executable
RUN chmod +x entrypoint.sh

# Command to run entrypoint script
CMD ["bash", "entrypoint.sh"]