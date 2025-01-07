import os
import json
from openai import AsyncOpenAI
from typing import Dict, Any
from datetime import datetime

class LLMAnalyzer:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI API anahtarı gerekli!")
        self.client = AsyncOpenAI(api_key=self.api_key)

    async def analyze(self, search_data: Dict, social_data: Dict, news_data: Dict) -> Dict[str, Any]:
        content = self._prepare_content(search_data, social_data, news_data)
        
        system_prompt = """Veri analiz uzmanı rolünde, aşağıdaki verilen bilgileri analiz edip, net ve özlü bir rapor hazırlayın. 
Analiz sonucunda, öznenin eylem ve söylemlerine dayanarak, Türkiye için tehdit analizi yapın ve sadece tek bir cümleyle 
TEHLİKELİ veya FAYDALI olarak değerlendirin."""

        user_prompt = """Lütfen şu veriler ışığında öznenin:
1. Kimliği ve pozisyonu
2. Önemli faaliyetleri ve eylemleri
3. İlişki ağı ve bağlantıları
4. Türkiye'ye etkisi

hakkında kısa bir analiz yapın. Tekrara düşmeden, veriye dayalı net bir profil çıkarın."""

        try:
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"VERİLER:\n\n{content}\n\n{user_prompt}"}
                ]
            )
            
            return {
                'analiz': response.choices[0].message.content,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            return {
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    def _prepare_content(self, search_data: Dict, social_data: Dict, news_data: Dict) -> str:
        content_parts = []

        # Arama sonuçlarından önemli içerikleri seç
        if 'articles' in search_data:
            content_parts.append("ARAMA BULGULARI:")
            for article in search_data['articles'][:3]:  # Sadece en alakalı 3 sonuç
                content_parts.append(f"• {article['content']}")

        # Sosyal medyadan önemli paylaşımları topla
        if 'platform_data' in social_data:
            content_parts.append("\nSOSYAL MEDYA AKTİVİTESİ:")
            for platform, posts in social_data['platform_data'].items():
                if posts:
                    content_parts.append(f"\n{platform.upper()}")
                    for post in posts[:2]:  # Her platformdan 2 önemli paylaşım
                        content_parts.append(f"• {post.get('description', '')}")

        # Haber kaynaklarından kritik bilgileri al
        if 'articles' in news_data:
            content_parts.append("\nHABER ANALİZİ:")
            for article in news_data['articles'][:3]:  # En güncel 3 haber
                content_parts.append(f"• {article['content']}")

        return "\n".join(content_parts)