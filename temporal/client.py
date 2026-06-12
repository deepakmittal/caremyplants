import os
from temporalio.client import Client
from temporal.workflows import GardenProcessingWorkflow

# Singleton client instance
temporal_client = None

async def get_temporal_client():
    global temporal_client
    if temporal_client is None:
        temporal_server_url = os.getenv("TEMPORAL_SERVER_URL", "localhost:7233")
        namespace = os.getenv("TEMPORAL_NAMESPACE", "default")
        use_tls = False
        if ":443" in temporal_server_url or "run.app" in temporal_server_url:
            use_tls = True
        temporal_client = await Client.connect(temporal_server_url, namespace=namespace, tls=use_tls)
    return temporal_client

async def start_garden_processing_workflow(update_id: int):
    client = await get_temporal_client()
    workflow_id = f"garden-update-{update_id}"
    
    # Start the workflow
    handle = await client.start_workflow(
        GardenProcessingWorkflow.run,
        update_id,
        id=workflow_id,
        task_queue="garden-processing-task-queue",
    )
    return handle.id
