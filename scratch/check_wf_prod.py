import asyncio
from temporalio.client import Client

async def main():
    try:
        url = "agentsmith-orchestrator-1059916488233.us-central1.run.app:443"
        client = await Client.connect(url, tls=True)
        handle = client.get_workflow_handle("garden-update-35")
        desc = await handle.describe()
        print("Workflow status in production:", desc.status)
        
        # Check history to see what happened
        async for event in handle.fetch_history():
            if event.HasField("workflow_execution_failed_event_attributes"):
                print("Failed event:", event.workflow_execution_failed_event_attributes.failure)
            elif event.HasField("workflow_execution_completed_event_attributes"):
                print("Completed event!")
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    asyncio.run(main())
