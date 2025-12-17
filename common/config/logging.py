# common/config/logging.py

import logging
import sys
from common.config.settings import get_settings

settings = get_settings()


def configure_logging():
    logging.basicConfig(
        level=settings.log_level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
