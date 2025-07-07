import os
import re
from pathlib import Path

import requests
from bs4 import Tag

from app.appcontext import AppContext
from app.usecases.crawling import CrawlingUsecase

from app.settings import settings

PAGENUMBERS_PATTERN = re.compile(r".*\d+/(?P<total_pages>\d+).*$")


class CrawlingImpl(CrawlingUsecase):
    def __init__(self, app: AppContext):
        self.http = app.helpers["http"]
        self.scraping = app.helpers["scraping"]
        self.logger = app.logger

    def invoke(self):
        # 1. クローリングして取得したファイルを置くディレクトリを作る (なければ)
        self._create_destdir()
        self.logger.info("出力先ディレクトリを作成")

        # 2. 作者の索引ページを取得する (あいうえお順?)
        for index_url in self._extract_index_url():
            self.logger.info("索引ページを取得: %s", index_url)
            if not isinstance(index_url, str):
                raise ValueError()

            # 3. 索引ページから作者のページを取得する (索引ページはページングがある)
            for author_url in self._extract_author_url(index_url):
                self.logger.info("作者ページを取得: %s", author_url)

                # 4. 作者のページから単行本のURLを得てページをダウンロードして保存
                for comic_url in self._extract_comic_url(author_url):
                    self.logger.info("単行本ページを取得: %s", comic_url)
                    if not isinstance(comic_url, str):
                        raise ValueError()
                    skipped = self._save_comic_html(comic_url)
                    if skipped:
                        self.logger.info("単行本ページを保存をスキップ: %s", comic_url)
                    else:
                        self.logger.info("単行本ページを保存: %s", comic_url)

    def _create_destdir(self):
        destpath = Path(settings.DEST_TITLE_DIR)
        if not destpath.exists():
            os.mkdir(destpath)

        if not destpath.is_dir():
            raise ValueError()

    def _extract_index_url(self):
        content = self.http.request(settings.MANGADB_INDEX_ROOT_URL)

        soup = self.scraping.soup(content)
        for atag in soup.find_all("a"):
            if not isinstance(atag, Tag):
                raise ValueError()
            url = atag.get("href")
            if url is None:
                raise ValueError()

            if "author/word-" in url:
                yield url

    def _extract_author_url(self, index_url: str):
        soup = self.scraping.soup(self.http.request(index_url))
        div = soup.find("div", {"class": "srh-result"})
        if div is None:
            raise ValueError()

        m = PAGENUMBERS_PATTERN.search(div.text)
        if m is None:
            raise ValueError()

        total_pages = int(m.group("total_pages"))

        for pn in range(1, total_pages + 1):
            author_list_url = index_url.replace(".html", f"-p{pn}.html")

            soup = self.scraping.soup(self.http.request(author_list_url))

            dltag = soup.find("dl", {"class": "author-list"})
            if not (dltag is not None and isinstance(dltag, Tag)):
                raise ValueError()

            for atag in dltag.find_all("a"):
                if not isinstance(atag, Tag):
                    raise ValueError()

                author_url = atag.get("href")
                if author_url is None:
                    raise ValueError()
                yield author_url

    def _extract_comic_url(self, author_url):
        try:
            author_content = self.http.request(author_url)
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return
            else:
                raise

        soup = self.scraping.soup(author_content)
        comic_section = soup.find("section", {"id": "book-clist"})
        if comic_section is None:
            return

        if not isinstance(comic_section, Tag):
            raise ValueError()
        for atag in comic_section.find_all("a"):
            if not isinstance(atag, Tag):
                raise ValueError()
            url = atag.get("href")
            if url is None:
                raise ValueError()
            if "/title/" in url:
                yield url

    def _save_comic_html(self, comic_url: str) -> bool:
        try:
            content = self.http.request(comic_url)
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return False
            else:
                raise

        destpath = os.path.join(
            settings.DEST_TITLE_DIR,
            os.path.basename(comic_url),
        )

        if os.path.exists(destpath) and os.path.isfile(destpath):
            return False

        with open(destpath, "wb") as fp:
            fp.write(content)

        return True
