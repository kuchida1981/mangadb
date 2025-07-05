import os
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from bs4 import BeautifulSoup

from app.appcontext import AppContext
from app.impl.crawling import CrawlingImpl, PAGENUMBERS_PATTERN
from app.settings import settings


class TestCrawlingImpl(unittest.TestCase):
    def setUp(self):
        self.app_context = AppContext(debug=True)
        self.http_mock = MagicMock()
        self.app_context.helpers["http"] = self.http_mock
        self.crawling_impl = CrawlingImpl(self.app_context)

    def test_create_destdir_if_not_exists(self):
        with patch("os.mkdir") as mkdir_mock:
            with patch("pathlib.Path.exists") as exists_mock:
                exists_mock.return_value = False
                self.crawling_impl._create_destdir()
                mkdir_mock.assert_called_once_with(Path(settings.DEST_TITLE_DIR))

    def test_create_destdir_if_exists(self):
        with patch("os.mkdir") as mkdir_mock:
            with patch("pathlib.Path.exists") as exists_mock:
                exists_mock.return_value = True
                self.crawling_impl._create_destdir()
                mkdir_mock.assert_not_called()

    def test_extract_index_url(self):
        html_content = """
        <html>
            <body>
                <a href="author/word-a.html">あ</a>
                <a href="author/word-i.html">い</a>
                <a href="other/page.html">other</a>
            </body>
        </html>
        """
        self.http_mock.request.return_value = html_content
        urls = list(self.crawling_impl._extract_index_url())
        self.assertEqual(len(urls), 2)
        self.assertIn("author/word-a.html", urls)
        self.assertIn("author/word-i.html", urls)

    def test_extract_author_url(self):
        html_content = """
        <html>
            <body>
                <div class="srh-result">100件中 1-50件表示 1/2ページ</div>
                <dl class="author-list">
                    <dd><a href="/author/123.html">Author 1</a></dd>
                    <dd><a href="/author/456.html">Author 2</a></dd>
                </dl>
            </body>
        </html>
        """
        self.http_mock.request.return_value = html_content
        urls = list(self.crawling_impl._extract_author_url("index.html"))
        self.assertEqual(len(urls), 4)  # 2 pages * 2 authors
        self.assertIn("/author/123.html", urls)
        self.assertIn("/author/456.html", urls)

    def test_extract_comic_url(self):
        html_content = """
        <html>
            <body>
                <section id="book-clist">
                    <a href="/title/111.html">Book 1</a>
                    <a href="/title/222.html">Book 2</a>
                    <a href="/other/333.html">Other</a>
                </section>
            </body>
        </html>
        """
        self.http_mock.request.return_value = html_content
        urls = list(self.crawling_impl._extract_comic_url("author.html"))
        self.assertEqual(len(urls), 2)
        self.assertIn("/title/111.html", urls)
        self.assertIn("/title/222.html", urls)

    def test_save_comic_html_new_file(self):
        comic_url = "http://example.com/title/123.html"
        dest_dir = settings.DEST_TITLE_DIR
        dest_path = os.path.join(dest_dir, "123.html")

        with patch("os.path.exists") as exists_mock:
            exists_mock.return_value = False
            with patch("builtins.open", unittest.mock.mock_open()) as mock_file:
                self.http_mock.request.return_value = b"test content"
                skipped = self.crawling_impl._save_comic_html(comic_url)
                self.assertFalse(skipped)
                mock_file.assert_called_once_with(dest_path, "wb")
                mock_file().write.assert_called_once_with(b"test content")

    def test_save_comic_html_existing_file(self):
        comic_url = "http://example.com/title/123.html"
        with patch("os.path.exists") as exists_mock, patch("os.path.isfile") as isfile_mock:
            exists_mock.return_value = True
            isfile_mock.return_value = True
            skipped = self.crawling_impl._save_comic_html(comic_url)
            self.assertTrue(skipped)
            self.http_mock.request.assert_not_called()

    def test_pagenumbers_pattern(self):
        text = "100件中 1-50件表示 1/2ページ"
        m = PAGENUMBERS_PATTERN.search(text)
        self.assertIsNotNone(m)
        self.assertEqual(m.group("total_pages"), "2")


if __name__ == "__main__":
    unittest.main()
