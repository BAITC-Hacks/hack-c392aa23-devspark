FROM node:20-alpine AS frontend-build

WORKDIR /build
COPY . ./
RUN if [ -f frontend/package.json ]; then \
      cd frontend && if [ -f package-lock.json ]; then npm ci; else npm install; fi && npm run build; \
    else \
      mkdir -p frontend/dist && printf '<!doctype html><title>Career Quest API</title>' > frontend/dist/index.html; \
    fi

FROM python:3.11-slim AS runtime

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/app ./app
COPY data ./data
COPY --from=frontend-build /build/frontend/dist ./frontend/dist

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
