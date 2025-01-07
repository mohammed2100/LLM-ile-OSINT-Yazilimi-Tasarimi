import logging
from typing import Dict, List
from bs4 import BeautifulSoup
from datetime import datetime
import urllib3
from urllib.parse import quote_plus
from collectors.base_collector import BaseCollector
import aiohttp
import ssl
import certifi

urllib3.disable_warnings()
logger = logging.getLogger(__name__)

class NewsCollector(BaseCollector):
    def __init__(self, ssl_context=None):
        super().__init__(ssl_context)
        
    async def _fetch_page(self, url: str) -> str:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'tr,en-US;q=0.7,en;q=0.3'
        }
        async with self.session.get(url, headers=headers, ssl=False, allow_redirects=True) as response:
            return await response.text()

    async def collect(self, target: str) -> Dict:
        await self.ensure_session()
        news_list = []
        query = target.translate(str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosucgiosu")).lower().replace(" ", "-")

        # Hürriyet
        try:
            hurriyet_url = f'https://www.hurriyet.com.tr/haberleri/{query}'
            html = await self._fetch_page(hurriyet_url)
            soup = BeautifulSoup(html, 'html.parser')
            news_items = soup.find_all('div', {'class': 'tag__list__item'})
            
            for item in news_items[:15]:
                try:
                    title_link = item.find('a', {'data-tag': 'h3'})
                    summary_link = item.find('a', {'data-tag': 'p'})
                    
                    if title_link and summary_link:
                        url = f"https://www.hurriyet.com.tr{title_link['href']}" if not title_link['href'].startswith('http') else title_link['href']
                        news_list.append({
                            'content': summary_link.p.text.strip(),
                            'url': url
                        })
                except:
                    continue

        except Exception as e:
            logger.error(f"Hürriyet hatası: {str(e)}")

        # Milliyet
        try:
            milliyet_url = f'https://www.milliyet.com.tr/haberleri/{query}'
            html = await self._fetch_page(milliyet_url)
            soup = BeautifulSoup(html, 'html.parser')
            news_items = soup.select('.news__item')
            
            for item in news_items[:15]:
                try:
                    link = item.select_one('a.news__link')
                    summary = item.select_one('.news__spot')
                    
                    if link and summary:
                        news_list.append({
                            'content': summary.text.strip(),
                            'url': f"https://www.milliyet.com.tr{link['href']}"
                        })
                except:
                    continue
                        
        except Exception as e:
            logger.error(f"Milliyet hatası: {str(e)}")

        # Sözcü
        try:
            sozcu_query = quote_plus(target)
            sozcu_url = f'https://www.sozcu.com.tr/arama?search={sozcu_query}'
            html = await self._fetch_page(sozcu_url)
            soup = BeautifulSoup(html, 'html.parser')
            news_items = soup.select('.col-md-6.col-lg-4.mb-4')
            
            for item in news_items[:15]:
                try:
                    link = item.select_one('a')
                    summary = item.select_one('.small.text-secondary.text-truncate-2')
                    
                    if link and summary:
                        url = f"https://www.sozcu.com.tr{link['href']}" if not link['href'].startswith('http') else link['href']
                        news_list.append({
                            'content': summary.text.strip(),
                            'url': url
                        })
                except:
                    continue

        except Exception as e:
            logger.error(f"Sözcü hatası: {str(e)}")

        return {'articles': news_list}