import unittest
from crawl import normalize_url, get_heading_from_html, get_first_paragraph_from_html, get_urls_from_html, get_images_from_html, extract_page_data

class TestCrawl(unittest.TestCase):
    def test_normalize_url(self):
        self.assertEqual(
            normalize_url("https://www.boot.dev/blog/path"),
            "www.boot.dev/blog/path",
        )

    def test_http_scheme(self):
        self.assertEqual(
            normalize_url("http://www.boot.dev/blog/path"),
            "www.boot.dev/blog/path",
        )

    def test_trailing_slash(self):
        self.assertEqual(
            normalize_url("https://www.boot.dev/blog/path/"),
            "www.boot.dev/blog/path",
        )

    def test_uppercase(self):
        self.assertEqual(
            normalize_url("https://WWW.Boot.Dev/blog/path"),
            "www.boot.dev/blog/path",
        )

    def test_query_string_ignored(self):
        self.assertEqual(
            normalize_url("https://www.boot.dev/blog/path?x=1"),
            "www.boot.dev/blog/path",
        )

    def test_fragment_ignored(self):
        self.assertEqual(
            normalize_url("https://www.boot.dev/blog/path#section"),
            "www.boot.dev/blog/path",
        )

    def test_no_path(self):
        self.assertEqual(normalize_url("https://www.boot.dev"), "www.boot.dev")

    def test_root_slash_only(self):
        self.assertEqual(normalize_url("https://www.boot.dev/"), "www.boot.dev")

    def test_get_heading_from_html_basic(self):
        input_body = "<html><body><h1>Test Title</h1></body></html>"
        self.assertEqual(get_heading_from_html(input_body), "Test Title")

    def test_get_heading_from_html_h2_fallback(self):
        input_body = "<html><body><h2>Sub Title</h2></body></html>"
        self.assertEqual(get_heading_from_html(input_body), "Sub Title")

    def test_get_heading_from_html_h1_preferred_over_h2(self):
        input_body = "<html><body><h2>Second</h2><h1>First</h1></body></html>"
        self.assertEqual(get_heading_from_html(input_body), "First")

    def test_get_first_paragraph_from_html_basic(self):
        input_body = "<html><body><p>First.</p><p>Second.</p></body></html>"
        self.assertEqual(get_first_paragraph_from_html(input_body), "First.")

    def test_get_first_paragraph_from_html_main_priority(self):
        input_body = """<html><body>
            <p>Outside paragraph.</p>
            <main>
                <p>Main paragraph.</p>
            </main>
        </body></html>"""
        self.assertEqual(get_first_paragraph_from_html(input_body), "Main paragraph.")

    def test_get_first_paragraph_from_html_main_without_p_falls_back(self):
        input_body = """<html><body>
            <p>Outside paragraph.</p>
            <main><div>No paragraph in main.</div></main>
        </body></html>"""
        self.assertEqual(get_first_paragraph_from_html(input_body), "Outside paragraph.")

    def test_get_urls_from_html_absolute(self):
        input_url = "https://crawler-test.com"
        input_body = '<html><body><a href="https://crawler-test.com"><span>Boot.dev</span></a></body></html>'
        actual = get_urls_from_html(input_body, input_url)
        self.assertEqual(actual, ["https://crawler-test.com"])

    def test_get_urls_from_html_relative(self):
        input_url = "https://crawler-test.com"
        input_body = '<html><body><a href="/path/one">Link</a></body></html>'
        actual = get_urls_from_html(input_body, input_url)
        self.assertEqual(actual, ["https://crawler-test.com/path/one"])

    def test_get_urls_from_html_multiple(self):
        input_url = "https://crawler-test.com"
        input_body = """<html><body>
            <a href="/one">One</a>
            <a href="https://other.com/two">Two</a>
            <a href="three">Three</a>
        </body></html>"""
        actual = get_urls_from_html(input_body, input_url)
        expected = [
            "https://crawler-test.com/one",
            "https://other.com/two",
            "https://crawler-test.com/three",
        ]
        self.assertEqual(actual, expected)

    def test_get_images_from_html_relative(self):
        input_url = "https://crawler-test.com"
        input_body = '<html><body><img src="/logo.png" alt="Logo"></body></html>'
        actual = get_images_from_html(input_body, input_url)
        self.assertEqual(actual, ["https://crawler-test.com/logo.png"])

    def test_get_images_from_html_absolute(self):
        input_url = "https://crawler-test.com"
        input_body = '<html><body><img src="https://cdn.example.com/a.png"></body></html>'
        actual = get_images_from_html(input_body, input_url)
        self.assertEqual(actual, ["https://cdn.example.com/a.png"])

    def test_get_images_from_html_multiple(self):
        input_url = "https://crawler-test.com"
        input_body = '<img src="/a.png"><img src="b.png"><img src="/c/d.png">'
        actual = get_images_from_html(input_body, input_url)
        expected = [
            "https://crawler-test.com/a.png",
            "https://crawler-test.com/b.png",
            "https://crawler-test.com/c/d.png",
        ]
        self.assertEqual(actual, expected)

    def test_extract_page_data_basic(self):
        input_url = "https://crawler-test.com"
        input_body = """<html><body>
            <h1>Test Title</h1>
            <p>This is the first paragraph.</p>
            <a href="/link1">Link 1</a>
            <img src="/image1.jpg" alt="Image 1">
        </body></html>"""
        actual = extract_page_data(input_body, input_url)
        expected = {
            "url": "https://crawler-test.com",
            "heading": "Test Title",
            "first_paragraph": "This is the first paragraph.",
            "outgoing_links": ["https://crawler-test.com/link1"],
            "image_urls": ["https://crawler-test.com/image1.jpg"],
        }
        self.assertEqual(actual, expected)

    def test_extract_page_data_multiple_links_and_images(self):
        input_url = "https://crawler-test.com"
        input_body = """<html><body>
            <h1>Title</h1>
            <main><p>Main paragraph.</p></main>
            <a href="/one">One</a>
            <a href="https://other.com/two">Two</a>
            <img src="/a.png">
            <img src="https://cdn.example.com/b.png">
        </body></html>"""
        actual = extract_page_data(input_body, input_url)
        expected = {
            "url": "https://crawler-test.com",
            "heading": "Title",
            "first_paragraph": "Main paragraph.",
            "outgoing_links": [
                "https://crawler-test.com/one",
                "https://other.com/two",
            ],
            "image_urls": [
                "https://crawler-test.com/a.png",
                "https://cdn.example.com/b.png",
            ],
        }
        self.assertEqual(actual, expected)


if __name__ == "__main__":
    unittest.main()