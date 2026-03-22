# --- Stage 1: Build Frontend ---
FROM node:18-slim AS frontend-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ .
RUN npm run build

# --- Stage 2: Backend & Final Image ---
FROM python:3.9-slim
WORKDIR /app

# Install system dependencies (for discovery tools if needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY . .

# Copy built frontend from previous stage
COPY --from=frontend-build /app/frontend/dist /app/frontend/dist

EXPOSE 5000

ENV FLASK_APP=app.py
ENV PORT=5000

CMD ["python", "app.py"]
