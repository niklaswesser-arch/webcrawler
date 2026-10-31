import asyncio
import aiohttp
from urllib.parse import urlsplit, urljoin, urlparse
from bs4 import BeautifulSoup, Tag
import requests


def normalize_url(url):
    part = urlsplit(url)
    full_path = f"{part.netloc}{part.path}"
    full_path = full_path.rstrip("/")
    return full_path.lower()

def get_heading_from_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    h_tag = soup.find("h1") or soup.find("h2")
    return h_tag.get_text(strip=True) if isinstance(h_tag, Tag) else ""

def get_first_paragraph_from_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    main = soup.find("main")
    p_tag = None
    if isinstance(main, Tag):
        p_tag = main.find("p")
    if p_tag is None:
        p_tag = soup.find("p")
    return p_tag.get_text(strip=True) if isinstance(p_tag, Tag) else ""

def get_urls_from_html(html, base_url):
    soup = BeautifulSoup(html, "html.parser")
    urls = []
    for a in soup.find_all("a"):
        href = a.get("href")
        if href:
            urls.append(urljoin(base_url, href))
    return urls

def get_images_from_html(html, base_url):
    soup = BeautifulSoup(html, "html.parser")
    images = []
    for img in soup.find_all("img"):
        src = img.get("src")
        if src:
            images.append(urljoin(base_url, src))
    return images

def extract_page_data(html: str, page_url: str):
    return {
        "url": page_url,
        "heading": get_heading_from_html(html),
        "first_paragraph": get_first_paragraph_from_html(html),
        "outgoing_links": get_urls_from_html(html, page_url),
        "image_urls": get_images_from_html(html, page_url),
    }

class AsyncCrawler:
    def __init__(self, base_url, max_concurrency=3, max_pages=25):
        self.base_url = base_url
        self.base_domain = urlparse(base_url).netloc
        self.page_data = {}
        self.visited = set()
        self.lock = asyncio.Lock()
        self.max_concurrency = max_concurrency
        self.max_pages = max_pages
        self.should_stop = False
        self.all_tasks = set()
        self.semaphore = asyncio.Semaphore(max_concurrency)
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()

    async def add_page_visit(self, normalized_url):
        async with self.lock:
            if self.should_stop:
                return False
            if normalized_url in self.visited:
                return False
            if len(self.visited) >= self.max_pages:
                self.should_stop = True
                print("Reached maximum number of pages to crawl.")
                return False
            self.visited.add(normalized_url)
            return True

    async def get_html(self, url):
       async with self.session.get(
            url, headers={"User-Agent": "BootCrawler/1.0"}
        ) as response:
            if response.status >= 400:
                raise Exception(f"got HTTP error: {response.status} {response.reason}")
            content_type = response.headers.get("content-type", "")
            if "text/html" not in content_type:
                raise Exception(f"got non-HTML response: {content_type}")
            return await response.text()

    async def crawl_page(self, current_url):
        if self.should_stop:
            return

        if urlparse(current_url).netloc != self.base_domain:
            return

        normalized = normalize_url(current_url)
        if not await self.add_page_visit(normalized):
            return

        async with self.semaphore:
            print(f"crawling: {current_url}")
            try:
                html = await self.get_html(current_url)
            except Exception as e:
                print(f"error crawling {current_url}: {e}")
                return

        data = extract_page_data(html, current_url)

        async with self.lock:
            self.page_data[normalized] = data

        tasks = []
        try:
            for url in data["outgoing_links"]:
                task = asyncio.create_task(self.crawl_page(url))
                self.all_tasks.add(task)
                tasks.append(task)
            await asyncio.gather(*tasks)
        finally:
            for task in tasks:
                self.all_tasks.discard(task)

    async def crawl(self):
        await self.crawl_page(self.base_url)
        return self.page_data


async def crawl_site_async(base_url, max_concurrency=3, max_pages=25):
    async with AsyncCrawler(base_url, max_concurrency, max_pages) as crawler:
        return await crawler.crawl()