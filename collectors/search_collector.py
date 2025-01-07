import logging
from typing import Dict, List
from bs4 import BeautifulSoup
from urllib.parse import quote, unquote
from fake_useragent import UserAgent
import asyncio
from .base_collector import BaseCollector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SearchCollector(BaseCollector):
    def __init__(self, ssl_context=None):
        super().__init__(ssl_context)
        self.ua = UserAgent()
        
    async def collect(self, target: str) -> Dict:
        await self.ensure_session()
        try:
            search_results = []
            
            # Ana arama için
            general_results = await self._search(target)
            search_results.extend(general_results)
            
            # PDF'ler için
            pdf_query = f"{target} filetype:pdf"
            pdf_results = await self._search(pdf_query)
            search_results.extend(pdf_results)
            
            # Tekrarları kaldır
            seen_urls = set()
            unique_results = []
            
            for result in search_results:
                url = result['url']
                if url not in seen_urls:
                    seen_urls.add(url)
                    unique_results.append(result)
            
            # NewsCollector formatında döndür
            return {
                'articles': unique_results
            }
            
        except Exception as e:
            logger.error(f"Search error: {str(e)}")
            return {'articles': []}

    async def _search(self, query: str) -> List[Dict]:
        """DuckDuckGo'dan arama yap"""
        try:
            url = f"https://html.duckduckgo.com/html/?q={quote(query)}&kl=tr-tr"
            headers = {'User-Agent': self.ua.random}
            
            async with self.session.get(url, headers=headers) as response:
                if response.status != 200:
                    return []
                    
                html = await response.text()
                return self._parse_results(html)
                
        except Exception as e:
            logger.error(f"Search error: {str(e)}")
            return []

    def _parse_results(self, html: str) -> List[Dict]:
        """Search sonuçlarını parse et"""
        soup = BeautifulSoup(html, 'html.parser')
        results = []

        for result in soup.select('.result')[:10]:  # İlk 10 sonuç
            try:
                link = result.select_one('.result__a')
                snippet = result.select_one('.result__snippet')

                if link and snippet:
                    # URL'yi temizle
                    url = link['href']
                    if '//duckduckgo.com/l/?uddg=' in url:
                        url = unquote(url.split('uddg=')[1].split('&')[0])
                    
                    # İçeriği al
                    content = snippet.get_text(strip=True)
                    
                    # İçerik yeterince uzunsa ekle
                    if len(content) > 50:
                        results.append({
                            'content': content,
                            'url': url
                        })
            except:
                continue
        
        return results