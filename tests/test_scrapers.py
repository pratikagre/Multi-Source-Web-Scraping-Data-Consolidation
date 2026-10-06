"""
Unit tests for source-specific HTML parsers without network dependencies.
"""

from bs4 import BeautifulSoup
from scrapers.books_scraper import BooksScraper
from scrapers.quotes_scraper import QuotesScraper

SAMPLE_BOOK_HTML = """
<article class="product_pod">
    <div class="image_container">
        <a href="catalogue/a-light-in-the-attic_1000/index.html"><img src="media/cache/2b/f0/2bf001115a1ce807bc6477294249214f.jpg" alt="A Light in the Attic" class="thumbnail"></a>
    </div>
    <p class="star-rating Three">
        <i class="icon-star"></i>
        <i class="icon-star"></i>
        <i class="icon-star"></i>
    </p>
    <h3><a href="catalogue/a-light-in-the-attic_1000/index.html" title="A Light in the Attic">A Light in the ...</a></h3>
    <div class="product_price">
        <p class="price_color">£51.77</p>
        <p class="instock availability">
            <i class="icon-ok"></i>
            In stock
        </p>
    </div>
</article>
"""

SAMPLE_QUOTE_HTML = """
<div class="quote" itemscope="" itemtype="http://schema.org/CreativeWork">
    <span class="text" itemprop="text">“The world as we have created it is a process of our thinking. It cannot be changed without changing our thinking.”</span>
    <span>by <small class="author" itemprop="author">Albert Einstein</small>
    <a href="/author/Albert-Einstein">(about)</a>
    </span>
    <div class="tags">
        Tags:
        <meta class="keywords" itemprop="keywords" content="change,deep-thoughts,thinking,world">
        <a class="tag" href="/tag/change/page/1/">change</a>
        <a class="tag" href="/tag/deep-thoughts/page/1/">deep-thoughts</a>
        <a class="tag" href="/tag/thinking/page/1/">thinking</a>
        <a class="tag" href="/tag/world/page/1/">world</a>
    </div>
</div>
"""


def test_parse_book():
    scraper = BooksScraper(delay=0)
    soup = BeautifulSoup(SAMPLE_BOOK_HTML, "lxml")
    article = soup.select_one("article.product_pod")
    page_url = "https://books.toscrape.com/index.html"

    result = scraper.parse_book(article, page_url)
    assert result is not None
    assert result["source"] == "Books to Scrape"
    assert result["name_or_title"] == "A Light in the Attic"
    assert (
        result["source_url"]
        == "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html"
    )
    assert result["price_raw"] == "£51.77"
    assert result["rating_raw"] == "star-rating Three"
    assert "In stock" in result["availability_raw"]


def test_parse_quote():
    scraper = QuotesScraper(delay=0)
    soup = BeautifulSoup(SAMPLE_QUOTE_HTML, "lxml")
    quote_div = soup.select_one("div.quote")
    page_url = "https://quotes.toscrape.com/page/1/"

    result = scraper.parse_quote(quote_div, page_url)
    assert result is not None
    assert result["source"] == "Quotes to Scrape"
    assert "The world as we have created it" in result["name_or_title"]
    assert result["author"] == "Albert Einstein"
    assert (
        result["source_url"] == "https://quotes.toscrape.com/author/Albert-Einstein"
    )
    assert result["tags"] == ["change", "deep-thoughts", "thinking", "world"]


def test_parse_book_missing_elements():
    scraper = BooksScraper(delay=0)
    incomplete_html = '<article class="product_pod"><h3><a title="Only Title"></a></h3></article>'
    soup = BeautifulSoup(incomplete_html, "lxml")
    article = soup.select_one("article.product_pod")

    result = scraper.parse_book(article, "https://books.toscrape.com/")
    assert result is not None
    assert result["name_or_title"] == "Only Title"
    assert result["price_raw"] is None
    assert result["rating_raw"] is None
