# Stage 1: Build the Web UI
FROM node:20-alpine AS ui-builder
WORKDIR /app
COPY mobile/package*.json ./
RUN npm install --legacy-peer-deps
COPY mobile/ .
RUN npx expo export -p web

# Stage 2: Final image combining Python, Nginx, and Supervisor
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    nginx \
    supervisor \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Copy Nginx and Supervisor configs
COPY nginx.conf /etc/nginx/nginx.conf
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Copy compiled Web UI static assets
COPY --from=ui-builder /app/dist /var/www/html

# Copy the requirements file into the container
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Make the entrypoint script executable (if needed for migration or scripts)
RUN chmod +x entrypoint.sh

# Expose the port the Nginx server runs on (Cloud Run default)
EXPOSE 8080

# Run supervisor to manage nginx and uvicorn backend
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
