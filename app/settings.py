from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    MANGADB_INDEX_ROOT_URL: str = "http://localhost/"
    DEST_TITLE_DIR: str = "tmp"
    HTTP_DEFAULT_COOKIES: dict[str, str] = {
        "adultcomic_dbsearch_net[bc]": "true"}
    HTTP_DELAY_SECONDS: float = 3.0
    COMICDB_JSON_PATH: str = "comicdb.json"


settings = Settings()
