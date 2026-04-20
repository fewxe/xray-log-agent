import asyncio
import logging
from app.config import settings
from app.services.xray_parser import parse_line
from app.services.log_reader import LogReader

logger = logging.getLogger(__name__)


class LogPublisher:
    def __init__(self, broker) -> None:
        self._broker = broker
        self._reader = LogReader()
        self._pending: list[str] = []
        self._broker_healthy = True

    async def run(self) -> None:
        logger.info(
            "Запуск publish loop | файл=%s subject=%s interval=%.1fs",
            settings.log_file,
            settings.nats_subject,
            settings.poll_interval,
        )
        while True:
            try:
                await self._process_once()
            except Exception:
                logger.exception("Неожиданная ошибка в publish loop")
            await asyncio.sleep(settings.poll_interval)

    async def health_check(self) -> None:
        while True:
            await asyncio.sleep(10)
            try:
                await self._broker._connection.flush(timeout=3)
                if not self._broker_healthy:
                    logger.info("NATS соединение восстановлено")
                    self._broker_healthy = True
            except Exception:
                if self._broker_healthy:
                    logger.error("NATS недоступен! Накоплено строк в буфере: %d", len(self._pending))
                    self._broker_healthy = False

    async def _process_once(self) -> None:
        new_lines = self._reader.read_new_lines()
        if new_lines:
            self._pending.extend(new_lines)

        if not self._pending:
            return

        if len(self._pending) > settings.max_pending:
            dropped = len(self._pending) - settings.max_pending
            logger.warning("Буфер переполнен, сбрасываю %d старых строк", dropped)
            self._pending = self._pending[dropped:]

        failed: list[str] = []
        published = 0

        for line in self._pending:
            entry = parse_line(line)
            if entry is None:
                continue
            try:
                await asyncio.wait_for(
                    self._broker.publish(entry.model_dump(mode="json"), subject=settings.nats_subject),
                    timeout=5.0,
                )
                published += 1
            except asyncio.TimeoutError:
                logger.warning("Таймаут публикации, строка отложена")
                failed.append(line)
            except Exception as e:
                logger.error("Ошибка публикации (%s), строка отложена", e)
                failed.append(line)

        self._pending = failed

        if published:
            logger.info(
                "Опубликовано %d | в буфере %d | всего строк было %d",
                published,
                len(self._pending),
                len(new_lines),
            )
