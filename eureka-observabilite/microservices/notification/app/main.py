"""Notification microservice - entry point.

Run:  uvicorn app.main:app --reload --port 8084
  or: python -m app.main

Variables d'environnement : PORT (8084), EUREKA_SERVER (http://localhost:8761/eureka),
HOST_NAME (localhost), EUREKA_ENABLED (true)
"""
import logging
import os
from contextlib import asynccontextmanager

import py_eureka_client.eureka_client as eureka_client
from fastapi import FastAPI

from app.routers import notification

logger = logging.getLogger("notification")

PORT = int(os.getenv("PORT", "8084"))
HOST_NAME = os.getenv("HOST_NAME", "localhost")
EUREKA_SERVER = os.getenv("EUREKA_SERVER", "http://localhost:8761/eureka")
EUREKA_ENABLED = os.getenv("EUREKA_ENABLED", "true").lower() != "false"
APP_VERSION = "1.0.0"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Enregistre le service dans Eureka au demarrage, le desenregistre a l'arret."""
    registered = False
    if EUREKA_ENABLED:
        base_url = f"http://{HOST_NAME}:{PORT}"
        try:
            await eureka_client.init_async(
                eureka_server=EUREKA_SERVER,
                app_name="notification",          # apparait en majuscules : NOTIFICATION
                instance_port=PORT,
                instance_host=HOST_NAME,
                instance_ip="127.0.0.1",
                health_check_url=f"{base_url}/health",
                status_page_url=f"{base_url}/info",
                home_page_url=f"{base_url}/",
            )
            registered = True
            logger.info("Eureka: NOTIFICATION enregistre sur le port %s", PORT)
        except Exception as exc:  # le service continue a repondre meme si Eureka est absent
            logger.warning("Eureka: echec de l'enregistrement (%s)", exc)
    yield
    if registered:
        await eureka_client.stop_async()


app = FastAPI(
    title="Notification Microservice API",
    version=APP_VERSION,
    description=(
        "Notification microservice (Python / FastAPI, no database). "
        "Only the hello endpoint is implemented; the notification logic is to be developed by students."
    ),
    contact={"name": "Badia Abouhdid"},
    servers=[{"url": f"http://localhost:{PORT}", "description": "Local"}],
    # Same URLs as the other microservices of the project
    docs_url="/swagger-ui",       # Swagger UI
    openapi_url="/v3/api-docs",   # OpenAPI JSON
    redoc_url="/redoc",           # alternative documentation
    lifespan=lifespan,
)

app.include_router(notification.router)


# ---- Observabilite (lus par Eureka) ----
@app.get("/health", tags=["Observabilite"], summary="Etat de sante du service")
def health() -> dict:
    return {"status": "UP"}


@app.get("/info", tags=["Observabilite"], summary="Informations sur le service")
def info() -> dict:
    return {"name": "notification", "version": APP_VERSION, "description": "Microservice de notifications"}


# TODO (students): if you add other routers, include them here.


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=PORT, reload=True)
