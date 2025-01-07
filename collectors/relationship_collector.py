# # collectors/relationship_collector.py

# from typing import Dict, Any
# from bs4 import BeautifulSoup
# import logging
# from .base_collector import BaseCollector
# import urllib3

# urllib3.disable_warnings()
# logger = logging.getLogger(__name__)

# class RelationshipCollector(BaseCollector):
#     def __init__(self, ssl_context=None):
#         super().__init__(ssl_context)
        
#         # İlişki tipleri ve açıklamaları
#         self.relationship_types = {
#             'family': 'Aile üyesi',
#             'friend': 'Arkadaş',
#             'work': 'İş bağlantısı',
#             'organization': 'Örgütsel bağlantı'
#         }
        
#     async def collect(self, target: str) -> Dict[str, Any]:
#         """Hedef kişinin ilişkilerini topla"""
#         await self.ensure_session()
#         relationships = {
#             'target': target,
#             'connections': [],
#             'metadata': {
#                 'total_connections': 0,
#                 'connection_types': {}
#             }
#         }

#         try:
#             # LinkedIn bağlantıları
#             work_connections = await self._collect_linkedin_connections(target)
#             relationships['connections'].extend(work_connections)
            
#             # Facebook ilişkileri
#             social_connections = await self._collect_facebook_connections(target)
#             relationships['connections'].extend(social_connections)
            
#             # Instagram bağlantıları
#             instagram_connections = await self._collect_instagram_connections(target)
#             relationships['connections'].extend(instagram_connections)
            
#             # Haber kaynaklarından bahsedilen kişiler
#             news_connections = await self._collect_news_connections(target)
#             relationships['connections'].extend(news_connections)

#             # Metrikleri hesapla
#             relationships['metadata'] = self._calculate_metrics(relationships['connections'])
            
#         except Exception as e:
#             logger.error(f"Veri toplama hatası: {str(e)}")

#         return relationships

#     async def _collect_linkedin_connections(self, target: str) -> list:
#         """LinkedIn'den iş bağlantılarını topla"""
#         connections = []
#         search_url = f"https://www.linkedin.com/search/results/people/?keywords={target}"
        
#         try:
#             async with self.session.get(search_url, ssl=False) as response:
#                 if response.status == 200:
#                     html = await response.text()
#                     soup = BeautifulSoup(html, 'html.parser')
#                     # LinkedIn profillerini bul
#                     profiles = soup.find_all('div', {'class': 'search-result__info'})
                    
#                     for profile in profiles[:5]:  # İlk 5 bağlantı
#                         try:
#                             name = profile.find('span', {'class': 'actor-name'}).text.strip()
#                             title = profile.find('p', {'class': 'subline-level-1'}).text.strip()
#                             url = profile.find('a', {'class': 'search-result__result-link'})['href']
                            
#                             connections.append({
#                                 'name': name,
#                                 'title': title,
#                                 'relationship_type': 'work',
#                                 'source': 'LinkedIn',
#                                 'url': f"https://www.linkedin.com{url}"
#                             })
#                         except:
#                             continue
#         except Exception as e:
#             logger.error(f"LinkedIn veri toplama hatası: {str(e)}")
            
#         return connections

#     async def _collect_facebook_connections(self, target: str) -> list:
#         """Facebook'tan sosyal bağlantıları topla"""
#         connections = []
#         search_url = f"https://www.facebook.com/search/people/?q={target}"
        
#         try:
#             async with self.session.get(search_url, ssl=False) as response:
#                 if response.status == 200:
#                     html = await response.text()
#                     soup = BeautifulSoup(html, 'html.parser')
#                     # Facebook profillerini bul
#                     profiles = soup.find_all('div', {'class': '_32mo'})
                    
#                     for profile in profiles[:5]:
#                         try:
#                             name = profile.text.strip()
#                             url = profile.parent['href']
                            
#                             connections.append({
#                                 'name': name,
#                                 'relationship_type': 'friend',
#                                 'source': 'Facebook',
#                                 'url': url
#                             })
#                         except:
#                             continue
#         except Exception as e:
#             logger.error(f"Facebook veri toplama hatası: {str(e)}")
            
#         return connections

#     async def _collect_instagram_connections(self, target: str) -> list:
#         """Instagram'dan bağlantıları topla"""
#         connections = []
#         search_url = f"https://www.instagram.com/web/search/topsearch/?query={target}"
        
#         try:
#             async with self.session.get(search_url, ssl=False) as response:
#                 if response.status == 200:
#                     data = await response.json()
#                     for user in data.get('users', [])[:5]:
#                         user_info = user.get('user', {})
#                         connections.append({
#                             'name': user_info.get('full_name', ''),
#                             'username': user_info.get('username', ''),
#                             'relationship_type': 'friend',
#                             'source': 'Instagram',
#                             'url': f"https://www.instagram.com/{user_info.get('username', '')}"
#                         })
#         except Exception as e:
#             logger.error(f"Instagram veri toplama hatası: {str(e)}")
            
#         return connections

#     async def _collect_news_connections(self, target: str) -> list:
#         """Haber kaynaklarından bahsedilen kişileri topla"""
#         connections = []
#         news_url = f"https://www.google.com/search?q={target}&tbm=nws"
        
#         try:
#             async with self.session.get(news_url, ssl=False) as response:
#                 if response.status == 200:
#                     html = await response.text()
#                     soup = BeautifulSoup(html, 'html.parser')
                    
#                     # Haberlerde geçen kişi isimlerini bul
#                     articles = soup.find_all('div', {'class': 'g'})
#                     for article in articles[:5]:
#                         try:
#                             title = article.find('h3').text
#                             snippet = article.find('div', {'class': 'VwiC3b'}).text
                            
#                             # İsim benzeri yapıları bul (basit bir yaklaşım)
#                             words = snippet.split()
#                             for i in range(len(words) - 1):
#                                 if words[i][0].isupper() and words[i+1][0].isupper():
#                                     name = f"{words[i]} {words[i+1]}"
#                                     if name != target and len(name) > 5:
#                                         connections.append({
#                                             'name': name,
#                                             'relationship_type': 'organization',
#                                             'source': 'News',
#                                             'context': title
#                                         })
#                         except:
#                             continue
#         except Exception as e:
#             logger.error(f"Haber veri toplama hatası: {str(e)}")
            
#         return connections

#     def _calculate_metrics(self, connections: list) -> Dict[str, Any]:
#         """Bağlantı metriklerini hesapla"""
#         metrics = {
#             'total_connections': len(connections),
#             'connection_types': {}
#         }
        
#         # Her tip için sayıları hesapla
#         for conn in connections:
#             rel_type = conn.get('relationship_type', 'unknown')
#             metrics['connection_types'][rel_type] = metrics['connection_types'].get(rel_type, 0) + 1
            
#         return metrics