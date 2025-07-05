import logging
from typing import TypedDict

from app.helpers import HttpHelper, ScrapingHelper
from app.usecases import CrawlingUsecase, ToDBUsecase


class Usecases(TypedDict):
    crawling: CrawlingUsecase
    todb: ToDBUsecase


class Helpers(TypedDict):
    http: HttpHelper
    scraping: ScrapingHelper


class AppContext:
    _debug: bool
    logger: logging.Logger
    usecases: Usecases
    helpers: Helpers

    def __init__(self, debug: bool):
        self._debug = debug
        self.logger = self._getlogger()

        self.helpers = {
            "http": HttpHelper(),
            "scraping": ScrapingHelper(),
        }

    def implementations(self, crawling: CrawlingUsecase, todb: ToDBUsecase):
        self.usecases = {
            "crawling": crawling,
            "todb": todb,
        }

    def _getlogger(self):
        logger = logging.getLogger(__name__)

        logger.setLevel(logging.DEBUG if self._debug else logging.INFO)

        ch = logging.StreamHandler()
        logger.addHandler(ch)

        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        ch.setFormatter(formatter)

        return logger
