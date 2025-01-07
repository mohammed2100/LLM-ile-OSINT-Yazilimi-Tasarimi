# collectors/base_collector.py
from typing import Dict, List
import aiohttp
import logging
from abc import ABC, abstractmethod
import ssl


class BaseCollector(ABC):
    def __init__(self, ssl_context: ssl.SSLContext = None):
        self.session = None
        self.ssl_context = ssl_context
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }

    async def ensure_session(self):
        if not self.session or self.session.closed:
            connector = aiohttp.TCPConnector(ssl=self.ssl_context) if self.ssl_context else None
            self.session = aiohttp.ClientSession(headers=self.headers, connector=connector)

    @abstractmethod
    async def collect(self, target: str) -> Dict:
        pass

    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()