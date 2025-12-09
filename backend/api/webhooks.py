"""
Lightweight webhook notifier stubs.
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


def send_webhook(event: str, payload: Dict[str, Any]) -> None:
    """
    Stub webhook sender; logs payload for now.
    """
    logger.info("Webhook event=%s payload=%s", event, payload)
