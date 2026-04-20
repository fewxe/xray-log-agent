import asyncio
import logging
from faststream import FastStream
from faststream.nats import NatsBroker
from app.config import settings
from app.services.publisher import LogPublisher

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

broker = NatsBroker(
    servers=settings.nats_url,
    max_reconnect_attempts=-1,
    reconnect_time_wait=2,
)
app = FastStream(broker)
publisher = LogPublisher(broker)


@app.after_startup
async def on_startup() -> None:
    asyncio.create_task(publisher.run())
    asyncio.create_task(publisher.health_check())
