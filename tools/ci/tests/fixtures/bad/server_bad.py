import logging

logger = logging.getLogger(__name__)


def handle(request, ocr_text, result):
    logger.info("got text %s", ocr_text)  # line 7
    logging.warning(
        "model said %s",
        result.model_output,
    )  # line 8
    print(request.body)  # line 12
    logger.debug(f"fields={result.extracted_fields}")  # line 13
