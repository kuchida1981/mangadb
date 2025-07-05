import os
import re
from pathlib import Path

from bs4 import BeautifulSoup, Tag

from app.appcontext import AppContext
from app.usecases.crawling import CrawlingUsecase

from ..settings import settings

PAGENUMBERS_PATTERN = re.compile(r".*\d+/(?P<total_pages>\d+).*$")


class CrawlingImpl(CrawlingUsecase):
    def __init__(self, app: AppContext):
        self.http = app.helpers["http"]
        self.logger = app.logger

    def invoke(self):

        # 1. クローリングして取得したファイルを置くディレクトリを作る (なければ)
        self._create_destdir()
        self.logger.info("出力先ディレクトリを作成")

        # 2. 作者の索引ページを取得する (あいうえお順?)
        for index_url in self._extract_index_url():
            self.logger.info("索引ページを取得: %s", index_url)
            assert isinstance(index_url, str)

            # 3. 索引ページから作者のページを取得する (索引ページはページングがある)
            for author_url in self._extract_author_url(index_url):
                self.logger.info("作者ページを取得: %s", author_url)

                # 4. 作者のページから単行本のURLを得てページをダウンロードして保存
                for comic_url in self._extract_comic_url(author_url):
                    self.logger.info("単行本ページを取得: %s", comic_url)
                    assert isinstance(comic_url, str)
                    skipped = self._save_comic_html(comic_url)
                    if not skipped:
                        self.logger.info("単行本ページを保存: %s", comic_url)
                    else:
                        self.logger.info("単行本ページを保存をスキップ: %s", comic_url)

    def _create_destdir(self):
        destpath = Path(settings.DEST_TITLE_DIR)
        if not destpath.exists():
            os.mkdir(destpath)

        assert destpath.is_dir()

    def _extract_index_url(self):
        content = self.http.request(settings.MANGADB_INDEX_ROOT_URL)
        soup = BeautifulSoup(content, "html.parser")
        for atag in soup.find_all("a"):
            assert isinstance(atag, Tag)
            url = atag.get("href")
            assert url is not None

            if "author/word-" in url:
                yield url

    def _extract_author_url(self, index_url: str):
        soup = BeautifulSoup(self.http.request(index_url), "html.parser")
        div = soup.find("div", {"class": "srh-result"})
        assert div is not None

        m = PAGENUMBERS_PATTERN.search(div.text)
        assert m is not None
        total_pages = int(m.group("total_pages"))

        for pn in range(1, total_pages + 1):
            author_list_url = index_url.replace(".html", f"-p{pn}.html")

            soup = BeautifulSoup(self.http.request(
                author_list_url), "html.parser")

            dltag = soup.find("dl", {"class": "author-list"})
            assert dltag is not None and isinstance(dltag, Tag)

            for atag in dltag.find_all("a"):
                assert isinstance(atag, Tag)

                author_url = atag.get("href")
                assert author_url is not None
                yield author_url

    def _extract_comic_url(self, author_url):
        soup = BeautifulSoup(self.http.request(author_url), "html.parser")
        comic_section = soup.find("section", {"id": "book-clist"})
        if comic_section is None:
            return

        assert isinstance(comic_section, Tag)
        for atag in comic_section.find_all("a"):
            assert isinstance(atag, Tag)
            url = atag.get("href")
            assert url is not None
            if "/title/" in url:
                yield url

    def _save_comic_html(self, comic_url: str) -> bool:
        content = self.http.request(comic_url)
        destpath = os.path.join(
            settings.DEST_TITLE_DIR,
            os.path.basename(comic_url),
        )

        if os.path.exists(destpath) and os.path.isfile(destpath):
            return True

        with open(destpath, "wb") as fp:
            fp.write(content)

        return False
