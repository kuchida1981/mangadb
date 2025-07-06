from bs4 import BeautifulSoup
from pydantic import BaseModel


class FindAllArgs(BaseModel):
    tag: str


class ScrapingHelper:
    def soup(self, content: bytes):
        return BeautifulSoup(content, "html.parser")
