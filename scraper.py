
try:
    from rich.console import Console
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich import box
except Exception:
    class Console:
        def print(self, *args, **kwargs):
            print(*args)
    class Table:
        def __init__(self, *a, **k):
            self._rows = []
        def add_column(self, *a, **k):
            pass
        def add_row(self, *a, **k):
            self._rows.append(a)
    class Progress:
        def __init__(self, *a, **k):
            pass
        def __enter__(self):
            return self
        def __exit__(self, *a):
            return False
        def add_task(self, *a, **k):
            return 1
        def update(self, *a, **k):
            pass
    SpinnerColumn = TextColumn = None
    box = None

try:
    from bs4 import BeautifulSoup
except Exception:
    BeautifulSoup = None
try:
    from seleniumbase import Driver
except Exception:
    Driver = None
from datetime import datetime
from datetime import timedelta
from dataclasses import dataclass
from typing import List, Optional
from urllib.parse import urljoin, quote_plus
import csv
import time
import random
import re
import os


console = Console()

@dataclass
class SearchResult:
    title: str
    location: str
    date: str
    url: str
    category: Optional[str] = ""


class SecurityChallengeError(Exception):
    """Custom exception for when a security challenge is detected."""
    pass


class FetchError(Exception):
    """Raised when a page cannot be fetched after retries."""
    pass

class SahibindenScraper:

    def __init__(self, proxy: Optional[str] = None):
        self.base_url = "https://www.sahibinden.com"
        self.original_data: List[SearchResult] = []
        self.filtered_data: List[SearchResult] = []
        self.driver = None
        self.proxy = proxy
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
        ]

    def convert_date_format(self, date_str: str) -> str:
        """Convert date with Turkish month to 'yyyy-mm-dd'"""
        tr_months = {
            "ocak": "01", "şubat": "02", "mart": "03", "nisan": "04", "mayıs": "05", "haziran": "06",
            "temmuz": "07", "ağustos": "08", "eylül": "09", "ekim": "10", "kasım": "11", "aralık": "12"
        }

        if not date_str:
            return date_str

        s = date_str.strip()
        lower = s.lower()

        # Handle relative words
        if 'bugün' in lower or 'saat' in lower or 'dakika' in lower or 'dk' in lower:
            return datetime.now().strftime('%Y-%m-%d')
        if 'dün' in lower:
            return (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

        parts = s.split()
        try:
            # Expect formats like '3 Haziran 2026'
            if len(parts) >= 3:
                day = parts[0]
                month_str = parts[1].lower()
                year = parts[2]
                month = tr_months.get(month_str, None)
                if month is None:
                    # try to remove diacritics by normalizing common variants
                    month = tr_months.get(month_str.replace('i', 'ı'), None)
                if month is None:
                    return s
                date_obj = datetime.strptime(f"{day} {month} {year}", '%d %m %Y')
                return date_obj.strftime('%Y-%m-%d')
            else:
                return s
        except Exception:
            return s
        
    def _ensure_driver(self):
        """Lazy initialization of the driver to reuse the session."""
        if self.driver is None:
            selected_agent = random.choice(self.user_agents)
            self.driver = Driver(uc=True, headless=True, agent=selected_agent, proxy=self.proxy)
            self.driver.set_page_load_timeout(30)
        return self.driver

    def close_driver(self):
        """Safely close the browser session."""
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass
            self.driver = None

    def _save_debug_html(self, content: str, prefix: str = "debug"):
        """Save page source to a file for debugging purposes."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        os.makedirs('downloaded_files', exist_ok=True)
        filename = os.path.join('downloaded_files', f"{prefix}_{timestamp}.html")
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            console.print(f"[dim yellow]Debug: HTML captured and saved to {filename}[/dim yellow]")
        except Exception as e:
            console.print(f"[red]Failed to save debug HTML: {e}[/red]")

    def fetch_page(self, url):
        """Fetch page source with retries and block detection, including button click."""
        max_retries = 3
        last_error = ""
        for attempt in range(max_retries):
            try:
                driver = self._ensure_driver()
                driver.uc_open_with_reconnect(url, reconnect_time=6)
                
                source = driver.page_source
                
                # Check if we are being blocked or challenged
                lowered_source = source.lower()
                challenge_terms = ["captcha", "robot", "olağan dışı erişim", "tarayıcınızı kontrol ediyoruz"]
                
                if any(term in lowered_source for term in challenge_terms):
                    self._save_debug_html(source, f"challenge_detected_attempt_{attempt+1}_before_click")
                    console.print("[yellow]Security challenge detected. Attempting to click 'Devam Et' button...[/yellow]")
                    
                    # Check for the "Devam Et" button and click it
                    if driver.is_element_visible("#btn-continue"):
                        driver.click("#btn-continue")
                        console.print("[green]Clicked 'Devam Et' button. Waiting for page to load...[/green]")
                        time.sleep(5) # Wait for the page to process the click and load new content
                        source = driver.page_source # Get updated page source
                        lowered_source = source.lower() # Update lowered_source
                        
                        # Re-check if the challenge persists after clicking
                        if any(term in lowered_source for term in challenge_terms):
                            self._save_debug_html(source, f"challenge_detected_attempt_{attempt+1}_after_click")
                            raise SecurityChallengeError("Security challenge persists after clicking 'Devam Et'.")
                        else:
                            console.print("[green]Challenge resolved after clicking 'Devam Et'.[/green]")
                    else:
                        console.print("[yellow]'Devam Et' button not found. Raising security challenge error.[/yellow]")
                        raise SecurityChallengeError("Security challenge detected, but 'Devam Et' button not found.")
                
                if not source or len(source) < 1000:
                    raise Exception("Incomplete page load or empty response")

                return source

            except (SecurityChallengeError, Exception) as e:
                last_error = str(e)
                if self.driver:
                    self._save_debug_html(self.driver.page_source, "fetch_error" if not isinstance(e, SecurityChallengeError) else "challenge_detected")
                self.close_driver() # Force fresh driver on next attempt
                if attempt < max_retries - 1:
                    sleep_time = (attempt + 1) * 5 + random.uniform(1, 3)
                    console.print(f"[yellow]Error fetching page: {e}. Retrying in {sleep_time:.2f} seconds... (Attempt {attempt + 1}/{max_retries})[/yellow]")
                    time.sleep(sleep_time)
                    continue
                
        console.print(f"[red]Failed to fetch {url}: {last_error}[/red]")
        raise FetchError(f"Failed to fetch {url}: {last_error}")
    
    def fetch_search_results(self, search_query: str, search_date: str) -> List[SearchResult]:

        all_results = []
        current_page_url = None

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True) as progress:

            task = progress.add_task(description="[bold yellow]Initializing browser & bypassing protection...[/bold yellow]", total=None)
            
            # Map human-friendly date choices to query parameters
            date_map = {
                'Last 24 hours': '1day',
                'Last 3 days': '3days',
                'Last 7 days': '7days',
                'Last 15 days': '15days',
                'Last 30 days': '30days'
            }
            search_date_param = date_map.get(search_date, f"{re.sub(r'\D', '', search_date)}days")

            # Properly URL-encode the query
            quoted_query = quote_plus(search_query)
            initial_url = f"{self.base_url}/is-ilanlari/istanbul?date={search_date_param}&pagingSize=50&query_text={quoted_query}"
            current_page_url = initial_url
            page_num = 1

            while True:
                progress.update(task, description=f"[bold blue]Fetching results from page {page_num}...[/bold blue] (Total found: {len(all_results)})")
                try:
                    content = self.fetch_page(current_page_url)
                except SecurityChallengeError as e:
                    console.print(f"[red]Security challenge: {e}[/red]")
                    break
                except Exception as e:
                    console.print(f"[red]Error fetching page: {e}[/red]")
                    break

                soup = BeautifulSoup(content, 'html.parser')

                # Check if the search results table is present on the page
                if not soup.find('table', id='searchResultsTable'):
                    if page_num == 1: # Only show error if it's the first page and no table
                        console.print("[red]Error: Could not find search results table on the page. Cloudflare bypass might have failed or website structure changed.[/red]")
                    break # No more results or bypass failed for this page

                current_page_results = self._extract_results(soup, current_page_url)
                all_results.extend(current_page_results)

                # Find the "next page" link
                next_page_link = None
                pagination_ul = soup.find('ul', class_='pageNaviButtons')
                if pagination_ul:
                    # Look for the 'Sonraki' (Next) link
                    next_li = pagination_ul.find('li', class_='prevNextBut')
                    if next_li:
                        next_a = next_li.find('a', title='Sonraki')
                        if next_a and next_a.get('href'):
                            next_page_link = urljoin(self.base_url, next_a.get('href'))

                if next_page_link and next_page_link != current_page_url: # Ensure we don't loop on the same page
                    current_page_url = next_page_link
                    page_num += 1
                else:
                    break # No more next page links

        return all_results

    def _extract_results(self, soup, url):
        results = []
        try:
            # Locate the table by its ID
            table = soup.find('table', id='searchResultsTable')
            if not table:
                return []

            # Extract the rows within the tbody of the table
            tbody = table.find('tbody', class_='searchResultsRowClass')
            if not tbody:
                return []

            rows = tbody.find_all('tr')

            # Extract data from each row
            for row in rows:
                if 'searchResultsItem' not in row.get('class', []):
                    continue

                try:
                    ad_title_tag = row.find('a', class_='classifiedTitle')
                    ad_date = row.find('td', class_='searchResultsDateValue')                                        
                    loc_raw = row.find('td', class_='searchResultsLocationValue')
                    ad_url = ad_title_tag['href'] if ad_title_tag and ad_title_tag.get('href') else None

                    if not all([ad_title_tag, ad_date, loc_raw, ad_url]):
                        continue

                    ad_title = ad_title_tag.get_text(strip=True)
                    ad_date = ad_date.get_text(strip=True).replace("\n\n", " ")
                    ad_date = self.convert_date_format(ad_date)

                    # Use get_text to build a robust location string
                    location = loc_raw.get_text(separator=', ').strip()

                    full_url = urljoin(self.base_url, ad_url)

                    results.append(
                        SearchResult(
                            title=ad_title,
                            location=location, 
                            date=ad_date,
                            url=full_url,
                            category=""
                        ))

                except Exception as e:
                    console.print(f"[yellow]Warning: Could not parse row: {str(e)}[/yellow]")
                    continue
                
            return results
        
        except Exception as e:
            console.print(f"[red]Error extracting results: {str(e)}[/red]")
            return []    

    def create_results_table(self, data: List[SearchResult], title: str) -> Table:
        console.print(f"[green]Successfully fetched {len(data)} results.[/green]")
        table = Table(
            title=title,
            box=box.ROUNDED,
            show_header=True,
            header_style="bold magenta",
            title_style="bold cyan",
            expand=True
        )
        
        table.add_column("Title", style="green", no_wrap=False)
        table.add_column("Location", style="blue")
        table.add_column("Date", style="magenta")
        table.add_column("URL", style="cyan", no_wrap=False)
        
        for item in data:
            table.add_row(
                item.title,
                item.location,
                item.date
                ,
                item.url
            )
            
        return table

    def filter_results(self, data: List[SearchResult],
                      excluded_keywords: Optional[List[str]] = None,
                      categories: Optional[List[str]] = None,
                      locations: Optional[List[str]] = None) -> List[SearchResult]:
        
        filtered = data.copy()

        if not excluded_keywords:
            excluded_keywords = ['GETIR', 'GETİR', 'GEMİLERİNE','GEMİLEREDE','GEMİLERE', 'GEMİLERİ', 'GEMİ',
                                 'ELEKTRİK','KURYE','çağrı','bayan','kadın','GÜVENLİK','KUAFÖRÜ', 'İMKANI',
                                 'ARACIYLA','Garson','Muhasebe','Şöför','Otel','KARGO', 'MOTOR', 'ARABANIZLA',
                                 'TRANSFER', 'YOLCU', 'Gemi', 'CİRO', 'KAZAN', 'ARAÇLARIYLA', 'aracıyla']
        
        filtered = [
                item for item in filtered 
                if not any(keyword.lower() in item.title.lower()
                          for keyword in excluded_keywords if keyword)
            ]
            
        if categories and categories[0] != '':
            filtered = [
                item for item in filtered 
                if any(category.lower() in item.category.lower() 
                      for category in categories if category)
            ]
            
        if locations and locations[0] != '':
            filtered = [
                item for item in filtered 
                if any(location.lower() in item.location.lower() 
                      for location in locations if location)
            ]
            
        return filtered

    def save_to_csv(self, data: List[SearchResult], filename: str):

        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Title', 'Location', 'Date', 'URL'])
            for item in data:
                writer.writerow([
                    item.title,
                    item.location,
                    item.date,
                    item.url
                ])
        console.print(f"[green]Successfully saved to {filename}[/green]")
