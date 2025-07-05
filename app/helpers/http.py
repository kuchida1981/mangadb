import time

import requests

from ..settings import settings


class HttpHelper:

    def __init__(self, delay_seconds: float = settings.HTTP_DELAY_SECONDS):
        self.delay_seconds = delay_seconds

    def request(self, url: str) -> bytes:
        res = requests.get(url, cookies=settings.HTTP_DEFAULT_COOKIES)
        res.raise_for_status()

        if self.delay_seconds > 0:
            time.sleep(self.delay_seconds)

        return res.content
