import asyncio
import logging
import ssl

from faststream import FastStream
from faststream.nats import NatsBroker
from faststream.security import BaseSecurity

from app.config import settings
from app.services.publisher import LogPublisher

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

ssl_ctx = ssl.create_default_context()
security = BaseSecurity(ssl_context=ssl_ctx)

broker = NatsBroker(
    servers=f"{settings.nats_url}:{settings.nats_port}",
    max_reconnect_attempts=-1,
    reconnect_time_wait=2,
    tls_hostname=settings.nats_tls_hostname,
    security=security,
    connect_timeout=5,
    token=settings.nats_token,
)
app = FastStream(broker)
publisher = LogPublisher(broker)


@app.after_startup
async def on_startup() -> None:
    asyncio.create_task(publisher.run())
    asyncio.create_task(publisher.health_check())


if __name__ == "__main__":
    asyncio.run(app.run())
