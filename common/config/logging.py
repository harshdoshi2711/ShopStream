# common/config/logging.py

import logging
import sys
from common.config.settings import get_settings

settings = get_settings()


class CorrelationIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        # Always guarantee correlation_id exists
        if not hasattr(record, "correlation_id"):
            record.correlation_id = "-"
        return True


def configure_logging():
    handler = logging.StreamHandler(sys.stdout)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | corr_id=%(correlation_id)s | %(message)s"
    )

    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(settings.log_level)

    # 🚨 CRITICAL FIX: prevent duplicate handlers on reload
    if not root.handlers:
        root.addHandler(handler)

    root.addFilter(CorrelationIdFilter())
