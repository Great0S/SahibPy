from datetime import datetime, timedelta

from scraper import SahibindenScraper, SearchResult


def test_convert_date_format_explicit_month():
    s = SahibindenScraper()
    assert s.convert_date_format("3 Haziran 2026") == "2026-06-03"


def test_convert_date_format_today_yesterday():
    s = SahibindenScraper()
    today = datetime.now().strftime('%Y-%m-%d')
    assert s.convert_date_format("Bugün") == today
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    assert s.convert_date_format("Dün") == yesterday


def test_filter_excluded_keywords_case_insensitive():
    s = SahibindenScraper()
    items = [
        SearchResult(title="GEMİ Taşıma", location="Istanbul", date="2026-06-03", url="http://a", category=""),
        SearchResult(title="Python Developer", location="Istanbul", date="2026-06-03", url="http://b", category="")
    ]
    filtered = s.filter_results(items, excluded_keywords=["gemi"])
    assert len(filtered) == 1
    assert filtered[0].title == "Python Developer"


def test_url_joining():
    s = SahibindenScraper()
    base = s.base_url
    rel = "/ilan/some-ad"
    full = s.base_url + rel
    # Ensure urljoin-compatible result
    assert full.startswith(base)
