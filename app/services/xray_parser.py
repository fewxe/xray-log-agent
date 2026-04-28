import logging
import re

from app.models.log_entry import LogEntry

logger = logging.getLogger(__name__)

_PATTERN = re.compile(
    r"(?P<timestamp>\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2}\.\d+) "
    r"from (?P<ip>[\d.]+):(?P<port>\d+) "
    r"accepted (?P<protocol>\w+):(?P<host>[^:]+):(?P<dst_port>\d+)"
    r".*?email:\s*(?P<user_id>\d+)"
)

def parse_line(line: str) -> LogEntry | None:
    m = _PATTERN.search(line)
    if not m:
        return None

    d = m.groupdict()
    try:
        return LogEntry(
            client_ip=d["ip"],
            destination=d["host"],
            port=int(d["dst_port"]),
            user_id=int(d["user_id"]),
        )
    except Exception as e:
        logger.warning("Не удалось распарсить строку: %s | ошибка: %s", line.strip(), e)
        return None
