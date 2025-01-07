# visualizer/network_visualizer.py

import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import aiohttp
from bs4 import BeautifulSoup
import requests
from io import BytesIO
import numpy as np
from typing import Dict
import sys
import os

# Collector'ları import et
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from collectors.search_collector import SearchCollector
from collectors.social_collector import SocialMediaCollector
from collectors.news_collector import NewsCollector

class NetworkVisualizer:
    def __init__(self, ssl_context=None):
        self.G = nx.Graph()
        self.fig = None
        self.ax = None
        self.ssl_context = ssl_context
        
    async def collect_all_data(self, target_name: str) -> Dict:
        """Tüm collectorlerden veri topla"""
        collectors = {
            'search': SearchCollector(ssl_context=self.ssl_context),
            'social': SocialMediaCollector(ssl_context=self.ssl_context),
            'news': NewsCollector(ssl_context=self.ssl_context)
        }
        
        results = {}
        for collector_name, collector in collectors.items():
            try:
                results[collector_name] = await collector.collect(target_name)
            except Exception as e:
                print(f"Hata ({collector_name}): {str(e)}")
                results[collector_name] = {}
                
        return results

    async def get_person_image(self, name: str) -> str:
        """Kişinin fotoğrafını DuckDuckGo'dan bul"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        search_url = f"https://duckduckgo.com/?q={name}+photo&iax=images&ia=images"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(search_url, headers=headers) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        img = soup.select_one('.tile--img__img')
                        if img and 'src' in img.attrs:
                            return img['src']
        except Exception as e:
            print(f"Fotoğraf arama hatası: {e}")
        return None

    def add_profile_photo(self, image_url: str, center_pos):
        """Profil fotoğrafını grafiğin merkezine ekle"""
        try:
            response = requests.get(image_url)
            img = plt.imread(BytesIO(response.content))
            
            height, width = img.shape[:2]
            center = (width//2, height//2)
            radius = min(width, height)//2
            
            y, x = np.ogrid[:height, :width]
            dist_from_center = np.sqrt((x - center[0])**2 + (y - center[1])**2)
            mask = dist_from_center <= radius
            
            circle_img = np.zeros_like(img)
            if len(img.shape) == 3:
                for i in range(3):
                    circle_img[:,:,i] = img[:,:,i] * mask
            else:
                circle_img = img * mask
                
            imagebox = OffsetImage(circle_img, zoom=0.1)
            ab = AnnotationBbox(imagebox, center_pos, frameon=False)
            self.ax.add_artist(ab)
            
        except Exception as e:
            print(f"Fotoğraf ekleme hatası: {e}")

    async def create_network(self, target_name: str):
        """Ağı oluştur ve görselleştir"""
        # Veri topla
        data = await self.collect_all_data(target_name)
        
        # Ana düğümü ekle
        self.G.add_node(target_name, type='person')
        
        # Sosyal medya verilerini ekle
        if 'social' in data and 'platform_data' in data['social']:
            for platform, posts in data['social']['platform_data'].items():
                if posts:
                    platform_name = platform.capitalize()
                    self.G.add_node(platform_name, type='platform')
                    self.G.add_edge(target_name, platform_name)
                    
                    for post in posts[:3]:  # Her platformdan en fazla 3 bağlantı
                        if 'url' in post:
                            username = post['url'].split('/')[-1]
                            self.G.add_node(username, type='connection')
                            self.G.add_edge(platform_name, username)

        # Haber verilerini ekle
        if 'news' in data and 'articles' in data['news']:
            for article in data['news']['articles'][:3]:
                if 'url' in article:
                    domain = article['url'].split('/')[2]
                    if domain not in self.G:
                        self.G.add_node(domain, type='news')
                        self.G.add_edge(target_name, domain)
        
        # Fotoğraf bul ve görselleştir
        image_url = await self.get_person_image(target_name)
        self.visualize(target_name, image_url)

    def visualize(self, target_name: str, image_url: str = None):
        """Ağı görselleştir"""
        self.fig, self.ax = plt.subplots(figsize=(15, 10))
        
        pos = nx.spring_layout(self.G, k=1, iterations=50)
        
        colors = {
            'platform': '#3498db',  # mavi
            'connection': '#95a5a6', # gri
            'news': '#2ecc71'       # yeşil
        }
        
        sizes = {
            'platform': 2000,
            'connection': 1000,
            'news': 1500
        }
        
        # Düğümleri çiz
        for node_type in colors:
            nodes = [node for node, attr in self.G.nodes(data=True) 
                    if attr.get('type') == node_type]
            if nodes:
                nx.draw_networkx_nodes(self.G, pos,
                                     nodelist=nodes,
                                     node_color=colors[node_type],
                                     node_size=sizes[node_type],
                                     alpha=0.7)
        
        # Bağlantıları çiz
        nx.draw_networkx_edges(self.G, pos, 
                             edge_color='#bdc3c7',
                             width=2,
                             alpha=0.5)
        
        # Etiketleri çiz
        labels = {node: node for node in self.G.nodes() if node != target_name}
        nx.draw_networkx_labels(self.G, pos, labels, 
                              font_size=8,
                              font_weight='bold')
        
        # Merkeze fotoğraf ekle
        if image_url:
            self.add_profile_photo(image_url, pos[target_name])
        
        plt.title("OSINT Network Analizi", pad=20)
        plt.axis('off')
        plt.show()

# Test için
async def main():
    import ssl
    import certifi
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    
    visualizer = NetworkVisualizer(ssl_context=ssl_context)
    await visualizer.create_network("hakan fidan")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())