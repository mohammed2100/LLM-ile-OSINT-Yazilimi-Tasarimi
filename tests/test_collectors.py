import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import json
import ssl
import certifi
from datetime import datetime
from collectors.search_collector import SearchCollector
from collectors.social_collector import SocialMediaCollector
from collectors.news_collector import NewsCollector
from analyzers.llm_analyzer import LLMAnalyzer
from dotenv import load_dotenv

load_dotenv()

async def analyze_target(name: str = "Abdullah ocalan"):
    print("\n=== OSINT Veri Toplama ve Analiz ===\n")
    
    # Konfigürasyonlar
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    openai_key = os.getenv('OPENAI_API_KEY')
    
    # Collectors ve Analyzer başlat
    collectors = {
        'search': SearchCollector(ssl_context=ssl_context),
        'social': SocialMediaCollector(ssl_context=ssl_context),
        'news': NewsCollector(ssl_context=ssl_context)
    }
    
    analyzer = LLMAnalyzer(api_key=openai_key)
    
    try:
        # Veri toplama
        results = {}
        for collector_name, collector in collectors.items():
            print(f"{collector_name.capitalize()} verisi toplanıyor...")
            try:
                results[collector_name] = await collector.collect(name)
                print(f"✓ {collector_name.capitalize()} verisi toplandı")
            except Exception as e:
                print(f"✗ Hata: {collector_name}: {str(e)}")
                results[collector_name] = {"error": str(e)}
        
        # Verileri kaydet
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        os.makedirs('outputs', exist_ok=True)
        
        raw_data_file = f'outputs/raw_data_{name.replace(" ", "_")}_{timestamp}.json'
        with open(raw_data_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
            
        print(f"\nHam veriler kaydedildi: {raw_data_file}")
        
        # LLM Analizi
        print("\nLLM Analizi başlatılıyor...")
        analysis = await analyzer.analyze(
            search_data=results.get('search', {}),
            social_data=results.get('social', {}),
            news_data=results.get('news', {})
        )
        
        # Analiz sonuçlarını kaydet
        analysis_file = f'outputs/analysis_{name.replace(" ", "_")}_{timestamp}.json'
        with open(analysis_file, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, ensure_ascii=False, indent=2)
            
        print(f"Analiz sonuçları kaydedildi: {analysis_file}")
        
        return {
            'raw_data': results,
            'analysis': analysis
        }
        
    except Exception as e:
        print(f"\nGenel hata: {str(e)}")
        return None
    
    finally:
        # Session'ları temizle
        for collector in collectors.values():
            if hasattr(collector, 'session') and collector.session:
                await collector.close()

if __name__ == "__main__":
    asyncio.run(analyze_target())