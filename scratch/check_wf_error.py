import asyncio
from temporalio.client import Client

async def main():
    try:
        url = "agentsmith-orchestrator-1059916488233.us-central1.run.app:443"
        client = await Client.connect(url, tls=True)
        print("Checking garden-update-42...")
        handle = client.get_workflow_handle("garden-update-42")
        desc = await handle.describe()
        print("Workflow status:", desc.status)
        
        history = await handle.fetch_history()
        print(f"Total events: {len(history.events)}")
        for event in history.events:
            event_type = event.WhichOneof("attributes")
            print(f"Event ID: {event.event_id}, Type: {event_type}")
            if event_type:
                attrs = getattr(event, event_type)
                if event_type == "activity_task_scheduled_event_attributes":
                    print(f"  Activity Name: {attrs.activity_type.name}")
                elif event_type == "activity_task_failed_event_attributes":
                    print(f"  Failure: {attrs.failure.message}")
                elif event_type == "workflow_task_failed_event_attributes":
                    print(f"  Failure: {attrs.failure.message}")
                elif event_type == "workflow_execution_failed_event_attributes":
                    print(f"  Failure: {attrs.failure.message}")
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    asyncio.run(main())
