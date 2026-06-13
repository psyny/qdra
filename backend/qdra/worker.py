import asyncio
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from qdra.infrastructure.db.session import AsyncSessionLocal
from qdra.infrastructure.db.models import ReasoningJob
from qdra.infrastructure.config.settings import settings
import redis.asyncio as redis
from datetime import datetime


async def process_job(job_id: str, session: AsyncSession):
    """Process a single graph reasoning job."""
    # Update job status to running
    await session.execute(
        update(ReasoningJob)
        .where(ReasoningJob.id == job_id)
        .values(status="running", started_at=datetime.utcnow())
    )
    await session.commit()

    try:
        # TODO: Implement actual graph reasoning logic
        # For now, simulate processing
        await asyncio.sleep(2)

        # Update job status to succeeded
        await session.execute(
            update(ReasoningJob)
            .where(ReasoningJob.id == job_id)
            .values(
                status="succeeded",
                finished_at=datetime.utcnow(),
                result=json.dumps({"result": "success"})
            )
        )
        await session.commit()
        print(f"Job {job_id} completed successfully")

    except Exception as e:
        # Update job status to failed
        await session.execute(
            update(ReasoningJob)
            .where(ReasoningJob.id == job_id)
            .values(
                status="failed",
                finished_at=datetime.utcnow(),
                error_message=str(e)
            )
        )
        await session.commit()
        print(f"Job {job_id} failed: {e}")


async def worker_loop():
    """Main worker loop that consumes jobs from Redis queue."""
    r = redis.from_url(settings.redis_url, decode_responses=True)

    print(f"Worker started, listening on queue: {settings.graph_job_queue}")

    while True:
        try:
            # Blocking pop from queue
            result = await r.blpop(settings.graph_job_queue, timeout=5)
            
            if result:
                _, job_id = result
                print(f"Received job: {job_id}")

                async with AsyncSessionLocal() as session:
                    await process_job(job_id, session)

        except Exception as e:
            print(f"Error in worker loop: {e}")
            await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(worker_loop())
