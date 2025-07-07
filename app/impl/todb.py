import json
from pathlib import Path
from typing import Annotated, Any

from bs4 import BeautifulSoup, Tag
from pydantic import BaseModel, Field, RootModel, field_validator

from app.appcontext import AppContext
from app.settings import settings
from app.usecases.todb import ToDBUsecase


class Author(BaseModel):
    name: str


class Publisher(BaseModel):
    name: str


class MainEntity(BaseModel):
    name: str
    authors: Annotated[list[Author], Field(alias="author")]
    publisher: Publisher
    keywords: list[str] | None = []

    @field_validator("keywords", mode="before")
    @classmethod
    def _keywords(cls, v):
        if isinstance(v, str):
            return [t.strip() for t in v.split(",")]
        return v


class SiteTitleLDJson(BaseModel):
    main_entity: Annotated[MainEntity, Field(alias="mainEntity")]
    description: str


class ToDBImpl(ToDBUsecase):
    def __init__(self, app: AppContext):
        self.logger = app.logger

    def invoke(self):
        dirpath = Path(settings.DEST_TITLE_DIR)
        dest_fp = open(settings.COMICDB_JSON_PATH, "w+")
        for p in dirpath.glob("*.html"):
            with open(p) as fp:
                soup = BeautifulSoup(fp.read(), "html.parser")

            script_ldjson_tag = soup.find(
                "script", {"type": "application/ld+json"})
            if script_ldjson_tag is None or not isinstance(script_ldjson_tag, Tag):
                raise ValueError()

            src = script_ldjson_tag.text
            src = src.replace("\n", "")

            item = RootModel[tuple[SiteTitleLDJson, Any, Any]
                             ].model_validate_json(src).root[0]
            json.dump(item.model_dump(), dest_fp)

        dest_fp.close()
