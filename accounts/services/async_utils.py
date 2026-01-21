import threading
import logging

logger = logging.getLogger(__name__)


def run_async(func, *args, **kwargs):
    """
    Run a function in a daemon thread (non-blocking).
    """
    try:
        thread = threading.Thread(
            target=func,
            args=args,
            kwargs=kwargs,
            daemon=True,
        )
        thread.start()
    except Exception as e:
        logger.exception(f"Async execution failed: {e}")
