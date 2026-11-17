FROM node:24-alpine AS web
WORKDIR /build
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
COPY --from=web /build/dist frontend/dist
CMD ["sh","-c","python seed.py && exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
