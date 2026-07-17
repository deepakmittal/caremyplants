import asyncio
from temporalio.client import Client

async def main():
    try:
        url = "agentsmith-orchestrator-1059916488233.us-central1.run.app:443"
        client = await Client.connect(url, tls=True)
        handle = client.get_workflow_handle("garden-update-35")
        desc = await handle.describe()
        print("Workflow status:", desc.status)
        print("Pending activities count:", len(desc.pending_activities))
        for act in desc.pending_activities:
            print(f"  Activity ID: {act.activity_id}, Name: {act.activity_type}, State: {act.state}")
            if act.last_failure:
                print(f"    Last Failure: {act.last_failure.message}")
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    asyncio.run(main())
