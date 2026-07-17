import asyncio
from temporalio.client import Client

async def main():
    try:
        url = "agentsmith-orchestrator-1059916488233.us-central1.run.app:443"
        client = await Client.connect(url, tls=True)
        handle = client.get_workflow_handle("garden-update-36")
        desc = await handle.describe()
        print("Workflow status in production:", desc.status)
        
        print("\n--- Event History ---")
        history = await handle.fetch_history()
        for event in history.events:
            event_type = event.WhichOneof("attributes")
            print(f"Event: {event_type}")
            if event_type == "workflow_execution_failed_event_attributes":
                print("  Failed:", event.workflow_execution_failed_event_attributes.failure.message)
            elif event_type == "activity_task_failed_event_attributes":
                print("  Activity Failed:", event.activity_task_failed_event_attributes.failure.message)
            elif event_type == "workflow_execution_completed_event_attributes":
                print("  Completed!")
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    asyncio.run(main())
