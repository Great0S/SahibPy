
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import box
from bs4 import BeautifulSoup
from seleniumbase import Driver
from datetime import datetime
from dataclasses import dataclass
from typing import List, Optional
from urllib.parse import urljoin
import csv
import re

import urllib


console = Console()

@dataclass
class SearchResult:
    title: str
    location: str
    date: str
    url: str


class SahibindenScraper:

    def __init__(self):
        self.base_url = "https://www.sahibinden.com"
        self.original_data: List[SearchResult] = []
        self.filtered_data: List[SearchResult] = []
        self.driver = None

    def convert_date_format(self, date_str: str) -> str:
        """Convert date with Turkish month to 'yyyy-mm-dd'"""
        
        tr_months = {
            "Ocak": "01", "Şubat": "02", "Mart": "03", "Nisan": "04", "Mayıs": "05", "Haziran": "06",
            "Temmuz": "07", "Ağustos": "08", "Eylül": "09", "Ekim": "10", "Kasım": "11", "Aralık": "12"
        }
        
        try:
            day, month_str, year = date_str.split()
            month = tr_months.get(month_str, month_str)
            date_obj = datetime.strptime(f"{day} {month} {year}", '%d %m %Y')
            return date_obj.strftime('%Y-%m-%d')
        except ValueError:
            return date_str
        
    def fetch_page(self, url):

        driver = Driver(uc=True, headless=True)
        try:

            # Open URL with a 6-second reconnect time to bypass the initial JS challenge
            driver.uc_open_with_reconnect(url, reconnect_time=4)

            # Return the page source
            return driver.page_source
        
        except Exception as e:
            return f"An error occurred: {e}"
        finally:
            driver.quit()
    
    def fetch_search_results(self, search_query: str, search_date: str) -> List[SearchResult]:

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True) as progress:

            task = progress.add_task(description="Handling Cloudflare...", total=None)
            
            if '24' in search_date:
                search_date = '1day'
            else:
                """Extract only digits from a string using regex"""
                search_date = f"{re.sub(r'\D', '', search_date)}days"

            url = f"{self.base_url}/is-ilanlari/istanbul?date={search_date}&pagingSize=50&query_text={search_query.replace(' ', '+')}"
                
            # Get page content using Cloudflare bypass
            content = self.fetch_page(url)
            
            if isinstance(content, str) and content.startswith("An error occurred"):
                console.print(f"[red]{content}[/red]")
                return []
            
            if isinstance(content, str) and "Could not find" in content:
                console.print(f"[red]{content}[/red]")
                return []
            
            progress.update(task, description="Parsing results...")
            
            soup = BeautifulSoup(content, 'html.parser')
            results = []

            # First page results
            results.extend(self._extract_results(soup, url))
            
            try:
                # Extract pages count
                pagination = soup.find('ul', class_='pageNaviButtons')
                paging_offset = 50

                if pagination:
                    pages = pagination.find_all('a')
                    current_offset = 50
                    
                    for page in pages:

                        page_url = urljoin(self.base_url, page.get('href'))
                        
                        if page.attrs.get('title') == "Sonraki":
                            pages = page_soup.find('ul', class_='pageNaviButtons').find_all('a')
                            paging_offset = 50
                            continue

                        if paging_offset < current_offset:
                            continue
                        
                        page_content = self.fetch_page(page_url)
                        page_soup = BeautifulSoup(page_content, 'html.parser')
                        results.extend(self._extract_results(page_soup, page_url))

                        query = urllib.parse.urlparse(page.get('href')).query
                        params = urllib.parse.parse_qs(query)
                        current_offset = int(params.get('pagingOffset', [0])[0])
                        paging_offset += 50
                    
                return results
            
            except Exception as e:
                console.print(f"[red]Error parsing results: {str(e)}[/red]")
                return []

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
                    ad_title = row.find('a', class_='classifiedTitle')
                    ad_date = row.find('td', class_='searchResultsDateValue')                                        
                    loc_raw = row.find('td', class_='searchResultsLocationValue')
                    ad_url = row.find('a', class_='classifiedTitle')['href']

                    if not all([ad_title, ad_date, loc_raw]):
                        continue

                    ad_title = ad_title.text.strip()
                    ad_date = ad_date.text.strip().replace("\n\n", " ")
                    ad_date = self.convert_date_format(ad_date)

                    if len(loc_raw.contents) > 1:
                        location = f"{loc_raw.contents[0].text.strip()}, {loc_raw.contents[2].text.strip()}"
                    else:
                        location = loc_raw.contents[0].text.strip()

                    results.append(
                        SearchResult(
                            title=ad_title,
                            location=location, 
                            date=ad_date,
                            url=f"{self.base_url + ad_url}"
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
        
        for item in data:
            table.add_row(
                item.title,
                item.location,
                item.date
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
