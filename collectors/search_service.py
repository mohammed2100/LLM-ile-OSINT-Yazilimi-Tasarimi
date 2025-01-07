# collectors/search_service.py
import logging
from typing import Dict, List
from bs4 import BeautifulSoup
from urllib.parse import quote, unquote
from fake_useragent import UserAgent
import asyncio

logger = logging.getLogger(__name__)

class SearchService:
    def __init__(self, session):
        self.session = session
        self.ua = UserAgent()
        self._last_request_time = 0
        self._delay = 1  # 1 saniye delay

    async def search(self, query: str, site_filter: str = "") -> List[Dict]:
        """DuckDuckGo üzerinden arama yap"""
        # Rate limiting
        now = asyncio.get_event_loop().time()
        if now - self._last_request_time < self._delay:
            await asyncio.sleep(self._delay - (now - self._last_request_time))
        
        try:
            final_query = f"{query} {site_filter}".strip()
            url = f"https://html.duckduckgo.com/html/?q={quote(final_query)}&kl=tr-tr"
            headers = {'User-Agent': self.ua.random}
            
            async with self.session.get(url, headers=headers) as response:
                self._last_request_time = asyncio.get_event_loop().time()
                
                if response.status != 200:
                    return []
                    
                html = await response.text()
                return self._parse_results(html)
                
        except Exception as e:
            logger.error(f"Search error: {str(e)}")
            return []

    def _parse_results(self, html: str) -> List[Dict]:
        """Arama sonuçlarını parse et"""
        soup = BeautifulSoup(html, 'html.parser')
        results = []
        
        for result in soup.select('.result'):
            try:
                link = result.select_one('.result__a')
                snippet = result.select_one('.result__snippet')
                
                if link and 'href' in link.attrs:
                    url = link['href']
                    if '//duckduckgo.com/l/?uddg=' in url:
                        url = unquote(url.split('uddg=')[1].split('&')[0])
                        
                    results.append({
                        'url': url,
                        'title': link.get_text(strip=True),
                        'content': snippet.get_text(strip=True) if snippet else ''
                    })
            except Exception:
                continue
                
        return results