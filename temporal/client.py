import os
import sys
import subprocess
import logging
from temporalio.client import Client
from temporalio.api.workflowservice.v1 import DescribeTaskQueueRequest
from temporalio.api.enums.v1 import TaskQueueType
from temporal.workflows import GardenProcessingWorkflow

logger = logging.getLogger("garden.temporal_client")

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
    
    # Check if there are active pollers on the task queue
    try:
        namespace = os.getenv("TEMPORAL_NAMESPACE", "default")
        req = DescribeTaskQueueRequest(
            namespace=namespace,
            task_queue={"name": "garden-processing-task-queue"},
            task_queue_type=TaskQueueType.TASK_QUEUE_TYPE_WORKFLOW
        )
        resp = await client.workflow_service.describe_task_queue(req)
        pollers = resp.pollers if resp else []
        logger.info(f"Active pollers on 'garden-processing-task-queue': {len(pollers)}")
        
        if not pollers:
            logger.warning("No active Temporal workers found. Starting a worker in the background...")
            # Start temporal_worker.py in a detached background process
            # Resolve the path to the workspace directory
            workspace_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            worker_script = os.path.join(workspace_dir, "temporal_worker.py")
            
            subprocess.Popen(
                [sys.executable, worker_script],
                cwd=workspace_dir,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )
            logger.info("Temporal worker background process spawned successfully.")
    except Exception as e:
        logger.error(f"Error checking/starting Temporal worker: {e}", exc_info=True)

    # Start the workflow
    handle = await client.start_workflow(
        GardenProcessingWorkflow.run,
        update_id,
        id=workflow_id,
        task_queue="garden-processing-task-queue",
    )
    return handle.id

