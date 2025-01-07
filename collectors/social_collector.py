from typing import Dict, Any, List, Optional
import aiohttp
import asyncio
from datetime import datetime
from .base_collector import BaseCollector
import logging
from bs4 import BeautifulSoup
import ssl
from urllib.parse import quote

class SocialMediaCollector(BaseCollector):
    def __init__(self, ssl_context: Optional[ssl.SSLContext] = None):
        super().__init__(ssl_context=ssl_context)
        self.base_url = "https://duckduckgo.com/html/?q={}"
        
    async def collect(self, target: str) -> Dict[str, Any]:
        await self.ensure_session()
        queries = [
            f'site:twitter.com {target}',
            f'site:linkedin.com/in/ {target}',
            f'site:instagram.com {target}'
        ]
        
        results = {
            'source': 'social_media',
            'timestamp': datetime.now().isoformat(),
            'query': target,
            'platform_data': {
                'twitter': [],
                'linkedin': [],
                'instagram': []
            },
            'metadata': {
                'total_results': 0,
                'successful_platforms': []
            }
        }
        
        for query in queries:
            try:
                platform = query.split(':')[1].split()[0].split('.')[0]
                search_results = await self._search_duckduckgo(query)
                if search_results:
                    results['platform_data'][platform] = search_results
                    results['metadata']['successful_platforms'].append(platform)
                    results['metadata']['total_results'] += len(search_results)
            except Exception as e:
                logging.error(f"Error searching {platform}: {str(e)}")
        
        return results
    
    async def _search_duckduckgo(self, query: str) -> List[Dict[str, Any]]:
        url = self.base_url.format(quote(query))
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://duckduckgo.com/',
            'DNT': '1'
        }
        
        try:
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    html = await response.text()
                    print(f"HTML alındı, uzunluk: {len(html)}")  # Debug
                    return self._parse_results(html)
                print(f"Status code: {response.status}")  # Debug
                return []
        except Exception as e:
            logging.error(f"DuckDuckGo search error: {str(e)}")
            return []

    def _parse_results(self, html: str) -> List[Dict[str, Any]]:
        soup = BeautifulSoup(html, 'html.parser')
        results = []

        # Debug için
        print(f"Bulunan sonuçlar: {len(soup.select('.result'))}")

        for result in soup.select('.result'):
            try:
                title = result.select_one('.result__title')
                link = result.select_one('.result__url')
                snippet = result.select_one('.result__snippet')
                
                if title and link:
                    results.append({
                        #'title': title.text.strip(),
                        'url': link.text.strip(),
                        'description': snippet.text.strip() if snippet else '',
                        #'mentions': self._find_mentions(snippet.text if snippet else ''),
                        #'hashtags': self._find_hashtags(snippet.text if snippet else '')
                    })
            except Exception as e:
                continue

        return results[:5]

    def _find_mentions(self, text: str) -> List[str]:
        import re
        return list(set(re.findall(r'@(\w+)', text)))
    
    def _find_hashtags(self, text: str) -> List[str]:
        import re
        return list(set(re.findall(r'#(\w+)', text)))