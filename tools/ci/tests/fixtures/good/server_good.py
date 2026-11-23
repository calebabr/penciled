"""Docstrings may mention print(ocr_text) without failing the check."""

import logging

logger = logging.getLogger(__name__)


def handle(ocr_text: str, item_count: int) -> int:
    # A comment about ocr_text is fine.
    logger.info("processed item count=%d", item_count)
    logger.warning("validation failed: reason=%s", "too_long")
    n = len(ocr_text)  # using content is fine; logging it is not
    return n
