from pydantic import BaseModel


class FindAllArgs(BaseModel):
    tag: str


class ScrapingHelper:
    def findall(self, args: FindAllArgs):
        pass
