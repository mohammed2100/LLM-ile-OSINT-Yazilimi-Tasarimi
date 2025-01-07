import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import asyncio
import sys
import os
from dotenv import load_dotenv
import json
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import ssl
import certifi
from datetime import datetime
import logging

# Logging ayarları
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# .env'den API key'i yükle
load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Path ayarlaması
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import collectors ve analyzers
from collectors.search_collector import SearchCollector
from collectors.social_collector import SocialMediaCollector
from collectors.news_collector import NewsCollector
from analyzers.llm_analyzer import LLMAnalyzer
from analyzers.network_analyzer import NetworkAnalyzer
from visualizer.network_visualizer import NetworkVisualizer

class OsintApp:
    def __init__(self, root):
        self.root = root
        self.root.title("OSINT Analiz Platformu")
        self.root.geometry("1200x800")

        # SSL context oluştur
        self.ssl_context = ssl.create_default_context(cafile=certifi.where())

        if not OPENAI_API_KEY:
            messagebox.showerror("Hata", "OpenAI API anahtarı bulunamadı!\nLütfen .env dosyasını kontrol edin.")
            root.destroy()
            return
        
        # Analyzer ve Visualizer'ı başlat
        self.network_analyzer = NetworkAnalyzer()
        self.visualizer = NetworkVisualizer()
        
        # Ana container
        main_container = ttk.PanedWindow(root, orient='horizontal')
        main_container.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Sol Panel
        left_frame = ttk.Frame(main_container)
        main_container.add(left_frame, weight=1)
        
        # Arama kısmı
        search_frame = ttk.LabelFrame(left_frame, text="Hedef Kişi/Kurum")
        search_frame.pack(padx=5, pady=5, fill='x')
        
        self.search_entry = ttk.Entry(search_frame, width=40)
        self.search_entry.pack(padx=5, pady=5)
        
        self.search_button = ttk.Button(search_frame, text="Analiz Et", command=self.run_analysis)
        self.search_button.pack(padx=5, pady=5)
        
        # Loading frame
        self.loading_frame = ttk.Frame(left_frame)
        self.progress = ttk.Progressbar(self.loading_frame, mode='indeterminate')
        self.progress.pack(fill='x', padx=5)
        
        # Analiz sonuçları
        result_frame = ttk.LabelFrame(left_frame, text="Analiz Raporu")
        result_frame.pack(padx=5, pady=5, fill='both', expand=True)
        
        self.result_text = scrolledtext.ScrolledText(result_frame)
        self.result_text.pack(padx=5, pady=5, fill='both', expand=True)
        
        # Sağ Panel
        right_frame = ttk.Frame(main_container)
        main_container.add(right_frame, weight=2)  # Sağ panel daha geniş
        
        # İstatistikler
        stats_frame = ttk.LabelFrame(right_frame, text="Veri İstatistikleri")
        stats_frame.pack(padx=5, pady=5, fill='x')
        
        self.stats_text = scrolledtext.ScrolledText(stats_frame, height=8)
        self.stats_text.pack(padx=5, pady=5, fill='both')
        
        # Görselleştirme alanı
        self.vis_frame = ttk.LabelFrame(right_frame, text="İlişki Ağı")
        self.vis_frame.pack(padx=5, pady=5, fill='both', expand=True)
        
        # Graf için Figure ve Canvas
        self.figure = Figure(figsize=(10, 8), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.vis_frame)
        self.canvas.get_tk_widget().pack(fill='both', expand=True)

        # Matplotlib toolbar
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.vis_frame)
        self.toolbar.update()

        # Tema ayarları
        style = ttk.Style()
        style.configure('TLabelframe', padding=5)

    def show_loading(self, show=True):
        if show:
            self.loading_frame.pack(pady=5)
            self.progress.start(10)
            self.search_button['state'] = 'disabled'
        else:
            self.progress.stop()
            self.loading_frame.pack_forget()
            self.search_button['state'] = 'normal'
            
    def run_analysis(self):
        target = self.search_entry.get().strip()
        if not target:
            messagebox.showwarning("Uyarı", "Lütfen bir hedef ismi girin.")
            return
            
        self.result_text.delete(1.0, tk.END)
        self.stats_text.delete(1.0, tk.END)
        self.figure.clear()
        self.show_loading(True)
        
        asyncio.run(self.analyze(target))

    async def analyze(self, target: str):
        try:
            collectors = {
                'search': SearchCollector(ssl_context=self.ssl_context),
                'social': SocialMediaCollector(ssl_context=self.ssl_context),
                'news': NewsCollector(ssl_context=self.ssl_context)
            }
            
            # Veri toplama
            results = {}
            for collector_name, collector in collectors.items():
                try:
                    results[collector_name] = await collector.collect(target)
                    logger.info(f"{collector_name.capitalize()} verisi toplandı")
                except Exception as e:
                    logger.error(f"Hata ({collector_name}): {str(e)}")
                    continue

            logger.info("Veri toplama tamamlandı")

            # Network analizi
            network_data = self.network_analyzer.analyze(
                target,
                results.get('search', {}),
                results.get('social', {}),
                results.get('news', {})
            )
            
            # Görselleştirme
            try:
                if network_data and 'nodes' in network_data:
                    logger.info("Görselleştirme başlatılıyor...")
                    self.visualizer.visualize(network_data, figure=self.figure)
                    self.canvas.draw()
                    logger.info("Görselleştirme tamamlandı")
                else:
                    logger.warning("İlişki ağı verisi oluşturulamadı")
            except Exception as e:
                logger.error(f"Görselleştirme hatası: {str(e)}")
                messagebox.showwarning("Uyarı", "İlişki ağı oluşturulurken hata oluştu.")

            # LLM Analizi
            analyzer = LLMAnalyzer(api_key=OPENAI_API_KEY)
            analysis = await analyzer.analyze(
                search_data=results.get('search', {}),
                social_data=results.get('social', {}),
                news_data=results.get('news', {})
            )
            
            # Analiz sonucunu göster
            if 'analiz' in analysis:
                self.result_text.insert(tk.END, analysis['analiz'])
            
            # İstatistikleri göster
            if network_data and 'metrics' in network_data:
                metrics = network_data['metrics']
                stats = f"""Toplanan Veri Özeti:
                
Toplam Bağlantı: {metrics['total_nodes']} düğüm
Toplam İlişki: {metrics['total_edges']} bağlantı
Arama Sonuçları: {len(results.get('search', {}).get('articles', []))} kaynak
Haber Kaynakları: {len(results.get('news', {}).get('articles', []))} haber
Sosyal Medya: {results.get('social', {}).get('metadata', {}).get('total_results', 0)} paylaşım

Bağlantı Tipleri:
"""
                for node_type, count in metrics['node_types'].items():
                    stats += f"- {node_type.capitalize()}: {count}\n"
                
                self.stats_text.insert(tk.END, stats)

            # Raporu kaydet
            self.save_report(target, results, analysis, network_data)

        except Exception as e:
            logger.error(f"Analiz hatası: {str(e)}")
            messagebox.showerror("Hata", f"Analiz sırasında hata oluştu:\n{str(e)}")
        
        finally:
            if 'collectors' in locals():
                for collector in collectors.values():
                    if hasattr(collector, 'session') and collector.session:
                        await collector.close()
            self.show_loading(False)

    def save_report(self, target: str, results: dict, analysis: dict, network_data: dict):
        try:
            report = {
                'target': target,
                'timestamp': datetime.now().isoformat(),
                'results': results,
                'analysis': analysis,
                'network_data': network_data
            }
            
            # reports klasörünü oluştur
            os.makedirs('reports', exist_ok=True)
            
            # Raporu kaydet
            filename = f"reports/report_{target}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
                
            logger.info(f"Rapor kaydedildi: {filename}")
                
        except Exception as e:
            logger.error(f"Rapor kaydetme hatası: {str(e)}")

def main():
    root = tk.Tk()
    app = OsintApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()