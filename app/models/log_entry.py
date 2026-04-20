from datetime import datetime
from pydantic import BaseModel


class LogEntry(BaseModel):
    client_ip: str
    destination: str
    port: int
    user_id: int
