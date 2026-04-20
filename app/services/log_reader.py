import os
import logging
from typing import IO
from app.config import settings

logger = logging.getLogger(__name__)


class LogReader:
    def __init__(self) -> None:
        self._file: IO[str] | None = None
        self._inode: int | None = None

    def read_new_lines(self) -> list[str]:
        """Возвращает завершённые строки, появившиеся с последнего вызова."""
        try:
            return self._read()
        except FileNotFoundError:
            self._close()
            return []
        except OSError as e:
            logger.error("Ошибка чтения лог-файла: %s", e)
            self._close()
            return []

    def _read(self) -> list[str]:
        inode = self._current_inode()

        if self._file is not None:
            if inode != self._inode:
                logger.info("Ротация лог-файла — переоткрываю (old=%s, new=%s)", self._inode, inode)
                self._close()
            elif self._is_truncated(self._file):
                logger.info("Лог-файл усечён — сбрасываю позицию")
                self._file.seek(0)

        if self._file is None:
            if inode is None:
                return []
            self._open(inode)
            assert self._file is not None

        return self._read_lines(self._file)

    def _read_lines(self, file: IO[str]) -> list[str]:
        return [line for line in file.readlines() if line.endswith("\n")]

    def _is_truncated(self, file: IO[str]) -> bool:
        try:
            return file.tell() > os.fstat(file.fileno()).st_size
        except OSError:
            return False

    def _open(self, inode: int) -> None:
        self._file = open(settings.log_file, "r")
        self._file.seek(0, 2)
        self._inode = inode
        logger.debug("Лог-файл открыт, inode=%s", inode)

    def _current_inode(self) -> int | None:
        try:
            return os.stat(settings.log_file).st_ino
        except FileNotFoundError:
            return None

    def _close(self) -> None:
        if self._file is None:
            return
        try:
            self._file.close()
        except OSError:
            pass
        self._file = None
        self._inode = None

    def __enter__(self) -> "LogReader":
        return self

    def __exit__(self, *_) -> None:
        self._close()
