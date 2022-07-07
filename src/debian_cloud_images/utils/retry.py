import logging

from time import sleep


def with_retries(fn, max_tries=10, retry_delay=10):
    success = False
    tries_remaining = max_tries
    while not success and tries_remaining > 0:
        tries_remaining -= 1
        try:
            return fn()
        except Exception:
            if tries_remaining == 0:
                raise
            logging.info('fn failed, will retry up to %d more times', tries_remaining)
            sleep(retry_delay)
