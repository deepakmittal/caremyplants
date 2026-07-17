import asyncio
from temporalio.client import Client

async def main():
    try:
        url = "agentsmith-orchestrator-1059916488233.us-central1.run.app:443"
        print(f"Connecting to Temporal at {url}...")
        client = await Client.connect(url, tls=True)
        print("Connected! Starting workflow for update 36...")
        
        handle = await client.start_workflow(
            "GardenProcessingWorkflow",
            36,
            id="garden-update-36",
            task_queue="garden-processing-task-queue",
        )
        print("Workflow started successfully! ID:", handle.id)
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    asyncio.run(main())
