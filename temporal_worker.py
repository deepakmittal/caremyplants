import asyncio
import os
import sys
import logging
from temporalio.client import Client
from temporalio.worker import Worker
from temporal.workflows import GardenProcessingWorkflow
from temporal.activities import (
    gather_garden_details,
    cut_plant_images,
    gather_plant_details,
    update_garden_flags,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("garden_temporal_worker")

async def main():
    temporal_server_url = os.getenv("TEMPORAL_SERVER_URL", "localhost:7233")
    namespace = os.getenv("TEMPORAL_NAMESPACE", "default")
    
    logger.info(f"Connecting to Temporal server at {temporal_server_url} (namespace: {namespace})...")
    from temporal.client import get_temporal_client
    client = await get_temporal_client()
    
    worker = Worker(
        client,
        task_queue="garden-processing-task-queue",
        workflows=[GardenProcessingWorkflow],
        activities=[
            gather_garden_details,
            cut_plant_images,
            gather_plant_details,
            update_garden_flags,
        ],
    )
    logger.info("Starting Garden Temporal Worker on task queue 'garden-processing-task-queue'...")
    await worker.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Worker stopped by user.")
        sys.exit(0)
