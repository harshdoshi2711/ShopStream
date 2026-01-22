# common/config/logging.py

import logging
import sys
from common.config.settings import get_settings

settings = get_settings()


class CorrelationIdFilter(logging.Filter):
    """
    Ensures every log record has a correlation_id attribute.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "correlation_id"):
            record.correlation_id = "-"
        return True


def configure_logging():
    handler = logging.StreamHandler(sys.stdout)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | corr_id=%(correlation_id)s | %(message)s"
    )

    handler.setFormatter(formatter)

    # 🔑 Attach filter to HANDLER (not just root logger)
    handler.addFilter(CorrelationIdFilter())

    root = logging.getLogger()
    root.setLevel(settings.log_level)

    # Avoid duplicate handlers on reload
    if not root.handlers:
        root.addHandler(handler)

    # 🔕 Reduce noisy third-party logs
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
