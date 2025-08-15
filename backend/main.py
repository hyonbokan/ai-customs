import multiprocessing
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from huey.consumer import Consumer

from api.router import router as api_router
from config import config
from core.utils.logger import logger
from task_queue import huey  # your Huey instance


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start Huey consumer with process workers
    workers = max(2, multiprocessing.cpu_count() - 1)  # Use N-1 cores, minimum 2
    consumer = Consumer(
        huey,
        workers=workers,  # Multiple workers to leverage CPU cores
        worker_type="process",
        check_worker_health=True,
        health_check_interval=10,
    )
    consumer.start()
    print(f"Huey consumer started with {workers} workers")

    yield  # Application runs

    # Shutdown consumer
    if consumer:
        consumer.stop()
        logger.info("Huey consumer stopped")
    else:
        logger.info("No Huey consumer to stop in non-production environment.")


# Initialize FastAPI app
app = FastAPI(
    title=config.app.TITLE,
    version=config.app.VERSION,
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[config.app.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Include API routes with correct prefix
app.include_router(api_router, prefix="/api")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=config.app.HOST,
        port=config.app.PORT,
        log_level="info",
    )
