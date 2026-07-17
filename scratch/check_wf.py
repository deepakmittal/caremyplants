import asyncio
from temporalio.client import Client

async def main():
    try:
        client = await Client.connect("localhost:7233")
        handle = client.get_workflow_handle("garden-update-34")
        desc = await handle.describe()
        print("Workflow status:", desc.status)
        
        # Print history to see failure reason
        async for event in handle.fetch_history():
            if event.HasField("workflow_execution_failed_event_attributes"):
                attr = event.workflow_execution_failed_event_attributes
                print("Failure:", attr.failure)
            elif event.HasField("workflow_execution_timed_out_event_attributes"):
                print("Timeout!")
            elif event.HasField("workflow_execution_completed_event_attributes"):
                print("Success!")
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    asyncio.run(main())
