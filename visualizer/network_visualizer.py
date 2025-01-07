# visualizer/network_visualizer.py

import networkx as nx
import matplotlib.pyplot as plt
from typing import Dict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NetworkVisualizer:
    def __init__(self):
        self.G = nx.Graph()
        
    def visualize(self, data: Dict, figure=None):
        """Ağı görselleştir"""
        try:
            if not data or 'nodes' not in data:
                logger.error("Geçersiz veri formatı")
                return
                
            # Graf verilerini oluştur
            self.G.clear()
            
            # Düğümleri ekle
            for node in data['nodes']:
                self.G.add_node(node['id'],
                              node_type=node['type'],
                              color=node['color'],
                              size=node['size'])
            
            # Kenarları ekle
            for edge in data['edges']:
                self.G.add_edge(edge['source'], edge['target'])

            # Görselleştirme
            if figure is not None:
                figure.clear()
                ax = figure.add_subplot(111)
            else:
                plt.figure(figsize=(15, 10))
                ax = plt.gca()
            
            # Layout hesapla
            pos = nx.spring_layout(self.G, k=1, iterations=50)
            
            # Düğümleri çiz
            for node, attr in self.G.nodes(data=True):
                nx.draw_networkx_nodes(self.G, pos,
                                     nodelist=[node],
                                     node_color=[attr['color']],
                                     node_size=attr['size'] * 50,
                                     alpha=0.9,
                                     edgecolors='white',
                                     linewidths=2,
                                     ax=ax)
            
            # Kenarları çiz
            nx.draw_networkx_edges(self.G, pos,
                                 edge_color='#cccccc',
                                 width=1,
                                 alpha=0.5,
                                 arrows=False,
                                 ax=ax)
            
            # Etiketleri çiz
            labels = {node: node for node in self.G.nodes()}
            nx.draw_networkx_labels(self.G, pos,
                                  labels,
                                  font_size=8,
                                  font_weight='bold',
                                  font_family='sans-serif',
                                  ax=ax)
            
            # Lejant
            legend_elements = []
            node_types = {
                'target': ('Hedef', '#FF6B6B'),
                'person': ('İlişkili Kişiler', '#FF6B6B'),
                'platform': ('Sosyal Medya', '#4ECDC4'),
                'news': ('Haber Kaynakları', '#2ecc71'),
                'account': ('Hesaplar', '#95a5a6'),
                'group': ('Gruplar', '#95a5a6')
            }
            
            for node_type, (label, color) in node_types.items():
                if any(attr['node_type'] == node_type for node, attr in self.G.nodes(data=True)):
                    legend_elements.append(plt.Line2D([0], [0],
                                                    marker='o',
                                                    color='w',
                                                    label=label,
                                                    markerfacecolor=color,
                                                    markersize=10,
                                                    markeredgecolor='white',
                                                    markeredgewidth=1))
            
            ax.legend(handles=legend_elements,
                     loc='upper left',
                     bbox_to_anchor=(1, 1),
                     fontsize=10)
            
            ax.set_title("OSINT Network Analizi", pad=20, size=14)
            ax.axis('off')
            
            if figure is not None:
                figure.tight_layout()
            else:
                plt.tight_layout()
            
            logger.info("Görselleştirme tamamlandı")
            
        except Exception as e:
            logger.error(f"Görselleştirme hatası: {str(e)}")
            raise