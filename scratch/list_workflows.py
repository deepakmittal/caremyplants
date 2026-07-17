import asyncio
from temporalio.client import Client

async def main():
    try:
        url = "agentsmith-orchestrator-1059916488233.us-central1.run.app:443"
        client = await Client.connect(url, tls=True)
        print("Connected! Listing workflows...")
        async for workflow in client.list_workflows():
            print(f"ID: {workflow.id}, Type: {workflow.workflow_type}, Status: {workflow.status}")
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    asyncio.run(main())
