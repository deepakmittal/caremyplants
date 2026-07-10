from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from temporal.activities import (
        gather_garden_details,
        cut_plant_images,
        gather_plant_details,
        update_garden_flags,
        generate_garden_visualization,
    )


# Retry policy configuration: maximum_attempts=1 disables all retries
NO_RETRY_POLICY = RetryPolicy(maximum_attempts=1)


@workflow.defn
class GardenProcessingWorkflow:
    @workflow.run
    async def run(self, update_id: int) -> str:
        """
        Executes the full garden processing workflow.
        """
        # 1. Gather garden-level details and identify plants
        garden_details_result = await workflow.execute_activity(
            gather_garden_details,
            update_id,
            start_to_close_timeout=timedelta(minutes=15),
            retry_policy=NO_RETRY_POLICY,
        )

        plants_list = garden_details_result["plants_list"]
        garden_id = garden_details_result["garden_id"]

        # 2. Cut plant images and create plant records
        plant_update_ids = await workflow.execute_activity(
            cut_plant_images,
            args=[update_id, garden_id, plants_list],
            start_to_close_timeout=timedelta(minutes=40),
            retry_policy=NO_RETRY_POLICY,
        )

        # 3. Gather details for each plant in parallel
        plant_detail_tasks = []
        for plant_update_id in plant_update_ids:
            task = workflow.execute_activity(
                gather_plant_details,
                plant_update_id,
                start_to_close_timeout=timedelta(minutes=15),
                retry_policy=NO_RETRY_POLICY,
            )
            plant_detail_tasks.append(task)

        # Wait for all plant detail tasks to complete
        if plant_detail_tasks:
            import asyncio
            await asyncio.gather(*plant_detail_tasks)


        # 4. Finalize the garden update
        await workflow.execute_activity(
            update_garden_flags,
            update_id,
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=NO_RETRY_POLICY,
        )

        # 5. Generate garden visualization
        await workflow.execute_activity(
            generate_garden_visualization,
            update_id,
            start_to_close_timeout=timedelta(minutes=15),
            retry_policy=NO_RETRY_POLICY,
        )

        return "COMPLETED"
