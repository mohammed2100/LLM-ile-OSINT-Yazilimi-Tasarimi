# analyzers/network_analyzer.py

import networkx as nx
from typing import Dict, Any
import re
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NetworkAnalyzer:
    def __init__(self):
        self.G = nx.Graph()
        
        # Node tipleri ve renkleri
        self.node_types = {
            'target': {'color': '#FF6B6B'},      # Kırmızı - Hedef
            'person': {'color': '#FFA07A'},      # Kırmızı - İlişkili kişiler
            'platform': {'color': '#4ECDC4'},    # Mavi - Sosyal medya platformları
            'news': {'color': '#2ecc71'},        # Yeşil - Haber kaynakları
            'account': {'color': '#95a5a6'},     # Gri - Sosyal medya hesapları
            'group': {'color': '#95a5a6'}        # Gri - Gruplar/Sayfalar
        }
        
        # Platform domain listesi
        self.news_domains = [
            'reuters.com', 'bbc.com', 'hurriyet.com.tr', 'milliyet.com.tr',
            'sozcu.com.tr', 'cnn.com', 'dw.com', 'aa.com.tr'
        ]

    def analyze(self, target: str, search_data: Dict, social_data: Dict, news_data: Dict) -> Dict[str, Any]:
        """Ana analiz fonksiyonu"""
        try:
            # Grafiği temizle
            self.G.clear()
            
            # Hedef düğümü ekle
            self.G.add_node(target, node_type='target', size=30)
            
            # Sosyal medya verilerini analiz et
            if 'platform_data' in social_data:
                self._analyze_social_connections(target, social_data['platform_data'])
            
            # Haber verilerini analiz et
            if 'articles' in news_data:
                self._analyze_news_connections(target, news_data['articles'])
            
            # Arama verilerini analiz et
            if 'articles' in search_data:
                self._analyze_search_connections(target, search_data['articles'])
            
            return {
                'nodes': self._get_nodes(),
                'edges': self._get_edges(),
                'metrics': self._calculate_metrics()
            }
            
        except Exception as e:
            logger.error(f"Analiz hatası: {str(e)}")
            return {'error': str(e)}

    def _analyze_social_connections(self, target: str, platform_data: Dict):
        """Sosyal medya bağlantılarını analiz et"""
        for platform, data in platform_data.items():
            if data:
                # Platform düğümünü ekle
                platform_name = platform.capitalize()
                self.G.add_node(platform_name, node_type='platform', size=25)
                self.G.add_edge(target, platform_name)
                
                # Platformdaki hesapları ve grupları analiz et
                for item in data:
                    if 'description' in item:
                        # Kullanıcı adlarını bul (@user gibi)
                        usernames = re.findall(r'@(\w+)', item['description'])
                        for username in usernames:
                            account_name = f"@{username}"
                            self.G.add_node(account_name, 
                                          node_type='account',
                                          size=15,
                                          platform=platform_name)
                            self.G.add_edge(platform_name, account_name)
                        
                        # Grup/sayfa isimlerini bul
                        groups = re.findall(r'([\w\s]+Group|[\w\s]+Page|[\w\s]+Community)', 
                                          item['description'])
                        for group in groups:
                            self.G.add_node(group.strip(), 
                                          node_type='group',
                                          size=15,
                                          platform=platform_name)
                            self.G.add_edge(platform_name, group.strip())

    def _analyze_news_connections(self, target: str, articles: list):
        """Haber bağlantılarını analiz et"""
        for article in articles:
            try:
                # Haber kaynağını ekle
                domain = article['url'].split('/')[2].replace('www.', '')
                if any(news_domain in domain for news_domain in self.news_domains):
                    self.G.add_node(domain, node_type='news', size=20)
                    self.G.add_edge(target, domain)
                
                # İçerikte geçen kişi isimlerini bul
                if 'content' in article:
                    # Büyük harfle başlayan 2-3 kelimelik isimler
                    names = re.findall(r'[A-Z][a-zıİğĞüÜşŞöÖçÇ]+(?:\s+[A-Z][a-zıİğĞüÜşŞöÖçÇ]+){1,2}',
                                     article['content'])
                    for name in names:
                        if name != target and len(name) > 5:  # Kısa isimleri filtrele
                            self.G.add_node(name.strip(), 
                                          node_type='person',
                                          size=20,
                                          source=domain)
                            self.G.add_edge(target, name.strip())
            except:
                continue

    def _analyze_search_connections(self, target: str, articles: list):
        """Arama sonuçlarından bağlantıları analiz et"""
        for article in articles:
            if 'content' in article:
                # Politik grupları bul
                groups = re.findall(r'([\w\s]+(Party|Group|Organization|Movement))',
                                  article['content'])
                for group in groups:
                    group_name = group[0].strip()
                    if group_name not in self.G:
                        self.G.add_node(group_name, 
                                      node_type='group',
                                      size=15)
                        self.G.add_edge(target, group_name)

    def _get_nodes(self) -> list:
        """Graf düğümlerini liste olarak döndür"""
        return [
            {
                'id': node,
                'label': node,
                'type': self.G.nodes[node]['node_type'],
                'color': self.node_types[self.G.nodes[node]['node_type']]['color'],
                'size': self.G.nodes[node].get('size', 15)
            }
            for node in self.G.nodes()
        ]

    def _get_edges(self) -> list:
        """Graf kenarlarını liste olarak döndür"""
        return [
            {
                'source': u,
                'target': v
            }
            for u, v in self.G.edges()
        ]

    def _calculate_metrics(self) -> Dict[str, Any]:
        """Graf metriklerini hesapla"""
        metrics = {
            'total_nodes': self.G.number_of_nodes(),
            'total_edges': self.G.number_of_edges(),
            'node_types': {}
        }
        
        # Düğüm tiplerini say
        for node, attr in self.G.nodes(data=True):
            node_type = attr.get('node_type', 'unknown')
            metrics['node_types'][node_type] = metrics['node_types'].get(node_type, 0) + 1
        
        return metrics