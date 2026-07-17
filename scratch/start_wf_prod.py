import asyncio
from temporalio.client import Client

async def main():
    try:
        url = "agentsmith-orchestrator-1059916488233.us-central1.run.app:443"
        print(f"Connecting to Temporal at {url}...")
        client = await Client.connect(url, tls=True)
        print("Connected! Starting workflow for update 35...")
        
        # Start the workflow
        # GardenProcessingWorkflow is defined in temporal.workflows
        # But we can start it using string name if we want, or just start it
        handle = await client.start_workflow(
            "GardenProcessingWorkflow",
            35,
            id="garden-update-35",
            task_queue="garden-processing-task-queue",
        )
        print("Workflow started successfully! ID:", handle.id)
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    asyncio.run(main())
