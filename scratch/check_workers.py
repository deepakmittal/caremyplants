import asyncio
from temporalio.client import Client

async def main():
    try:
        url = "agentsmith-orchestrator-1059916488233.us-central1.run.app:443"
        client = await Client.connect(url, tls=True)
        print("Connected! Describing task queue...")
        
        # Describe Workflow Task Queue
        desc_wf = await client.describe_task_queue(
            task_queue="garden-processing-task-queue"
        )
        print("Workflow pollers:")
        for poller in desc_wf.pollers:
            print(f"  Identity: {poller.identity}, Last access: {poller.last_access_time}")
            
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    asyncio.run(main())
