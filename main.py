#!/usr/bin/env python3
import asyncio

# from prometheus_client import make_asgi_app, Counter, Histogram
import time

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from contextlib import asynccontextmanager
import logging

from config import settings
from src.api.achievement import router as achievement_router
from src.api.auth import router as auth_router
from src.api.profile import router as profile_router
from src.api.rating import router as rating_router
from src.api.task import router as task_router
from src.api.user_activity import router as activity_router
from src.api.quests import router as quests_router
from src.admin import setup_admin


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Run database migrations on startup
    try:
        from src.migrations.runner import run_all_migrations
        await run_all_migrations()
    except Exception as e:
        logging.getLogger("uvicorn.error").error(f"Migration error during startup: {e}")
    yield


app = FastAPI(lifespan=lifespan)

# Trust X-Forwarded-Proto, X-Forwarded-For from reverse proxies (fixes HTTPS mixed-content and form action)
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")

# # Добавьте Prometheus middleware
# metrics_app = make_asgi_app()
# app.mount("/metrics", metrics_app)

# # Создайте метрики
# REQUEST_COUNT = Counter(
#     'request_count', 'App Request Count',
#     ['method', 'endpoint', 'http_status']
# )
# REQUEST_LATENCY = Histogram(
#     'request_latency_seconds', 'Request latency',
#     ['method', 'endpoint']
# )

# @app.middleware("http")
# async def monitor_requests(request, call_next):
#     start_time = time.time()
#     method = request.method
#     endpoint = request.url.path

#     try:
#         response = await call_next(request)
#     except Exception:
#         REQUEST_COUNT.labels(method, endpoint, 500).inc()
#         raise

#     latency = time.time() - start_time
#     REQUEST_LATENCY.labels(method, endpoint).observe(latency)
#     REQUEST_COUNT.labels(method, endpoint, response.status_code).inc()

#     return response

# CORS configuration
origins = []

if settings.FRONTEND_URL:
    clean_url = settings.FRONTEND_URL.strip('\"\'')
    origins.append(clean_url)
    if clean_url.startswith("http://"):
        origins.append(clean_url.replace("http://", "https://"))

if settings.CORS_ORIGINS:
    origins.extend([o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()])

# Add common Docker development URLs
origins.extend(
    [
        "http://localhost",
        "http://localhost:80",
        "http://localhost:9000",
        "http://frontend:9000",
        "http://nginx",
        "http://nginx:80",
        "http://backend:8000",
        "http://192.168.146.1:9000",
        "http://sqlfront.ru",
        "https://sqlfront.ru",
        "http://sql-front.mirea.ru",
        "https://sql-front.mirea.ru"
    ]
)

# Deduplicate
origins = list(set(origins))

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

app.include_router(auth_router)
app.include_router(achievement_router)
app.include_router(profile_router)
app.include_router(task_router)
app.include_router(rating_router)
app.include_router(activity_router)
app.include_router(quests_router)

# Initialize SQLAdmin administration panel
admin = setup_admin(app)


async def run_server(app, port):
    config = uvicorn.Config(
        app, host="0.0.0.0", port=port, proxy_headers=True, forwarded_allow_ips="*"
    )
    server = uvicorn.Server(config)
    await server.serve()


async def main():
    await run_server("main:app", 8000)


if __name__ == "__main__":
    asyncio.run(main())
