import requests
from requests.sessions import HTTPAdapter
from urllib3.util.retry import Retry

from app.settings import settings


class HttpHelper:

    session: requests.Session

    def __init__(self, delay_seconds: float = settings.HTTP_DELAY_SECONDS):

        session = requests.Session()
        retries = Retry(
            total=10,
            backoff_factor=delay_seconds,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        session.mount("https://", HTTPAdapter(max_retries=retries))
        self.session = session

    def request(self, url: str) -> bytes:
        res = self.session.get(url, cookies=settings.HTTP_DEFAULT_COOKIES)
        res.raise_for_status()

        return res.content
