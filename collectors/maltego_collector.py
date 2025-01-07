# collectors/whois_collector.py
import whois
from typing import Dict, Any, List
import asyncio
from .base_collector import BaseCollector
import logging


class WhoisCollector(BaseCollector):
    def __init__(self, ssl_context=None):
        super().__init__(ssl_context)
        
    async def collect(self, target: str) -> Dict[str, Any]:
        domains = await self._find_related_domains(target)
        results = {
            'source': 'whois',
            'timestamp': datetime.now().isoformat(),
            'query': target,
            'domain_data': {}
        }
        
        for domain in domains:
            try:
                whois_data = whois.whois(domain)
                results['domain_data'][domain] = {
                    'registrar': whois_data.registrar,
                    'creation_date': whois_data.creation_date,
                    'expiration_date': whois_data.expiration_date,
                    'name_servers': whois_data.name_servers,
                    'status': whois_data.status,
                    'emails': whois_data.emails
                }
            except Exception as e:
                logging.error(f"Whois error for {domain}: {str(e)}")
        
        return results
    
    async def _find_related_domains(self, target: str) -> List[str]:
        """Hedefle ilgili domain'leri bul"""
        # Burada search_collector'dan gelen verilerden domain çıkarımı yapılabilir
        # Örnek domainler:
        domains = [
            f"{target.replace(' ', '')}.com",
            f"{target.replace(' ', '')}.org",
            f"{target.replace(' ', '')}.net"
        ]
        return domains

# collectors/email_collector.py
class EmailCollector(BaseCollector):
    def __init__(self, api_key: str, ssl_context=None):
        super().__init__(ssl_context)
        self.api_key = api_key
        self.base_url = "https://api.hunter.io/v2"
        
    async def collect(self, target: str) -> Dict[str, Any]:
        domains = await self._find_related_domains(target)
        results = {
            'source': 'email_hunter',
            'timestamp': datetime.now().isoformat(),
            'query': target,
            'email_data': {}
        }
        
        async with aiohttp.ClientSession() as session:
            for domain in domains:
                try:
                    params = {
                        'domain': domain,
                        'api_key': self.api_key
                    }
                    async with session.get(f"{self.base_url}/domain-search", params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            results['email_data'][domain] = {
                                'emails': data.get('data', {}).get('emails', []),
                                'pattern': data.get('data', {}).get('pattern', ''),
                                'organization': data.get('data', {}).get('organization', '')
                            }
                except Exception as e:
                    logging.error(f"Hunter.io error for {domain}: {str(e)}")
        
        return results

    async def _find_related_domains(self, target: str) -> List[str]:
        """Hedefle ilgili domain'leri bul"""
        # Whois collector ile aynı mantık
        domains = [
            f"{target.replace(' ', '')}.com",
            f"{target.replace(' ', '')}.org",
            f"{target.replace(' ', '')}.net"
        ]
        return domains
    
