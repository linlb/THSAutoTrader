import logging
import threading
import time


def trace_gui_step(name, operation, *args, **kwargs):
    logger = logging.getLogger('FileLogger')
    thread_id = threading.get_ident()
    started = time.monotonic()
    logger.info("GUI步骤开始: %s, 线程=%s", name, thread_id)
    try:
        result = operation(*args, **kwargs)
    except Exception:
        logger.exception("GUI步骤失败: %s, 线程=%s, 耗时=%.3fs", name, thread_id, time.monotonic() - started)
        raise
    logger.info("GUI步骤结束: %s, 线程=%s, 耗时=%.3fs", name, thread_id, time.monotonic() - started)
    return result
