#!/usr/bin/env python3
"""
🔄 CASHBACKITO - Scraper Automatique
Scrape les taux de cashback toutes les heures via GitHub Actions
"""

import requests
from bs4 import BeautifulSoup
import json
import re
import time
import random
from datetime import datetime
from pathlib import Path

# Configuration
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
}

# Liste des marchands à scraper (nom, slug URL, catégorie, emoji)
MERCHANTS = [
    # Marketplace
    ("AliExpress", "aliexpress", "Marketplace", "🛒"),
    ("Amazon", "amazon", "Marketplace", "📦"),
    ("Cdiscount", "cdiscount", "Marketplace", "🏷️"),
    ("Rakuten", "rakuten", "Marketplace", "🎁"),
    
    # High-Tech
    ("Fnac", "fnac", "High-Tech", "🎮"),
    ("Darty", "darty", "High-Tech", "📺"),
    ("Boulanger", "boulanger", "High-Tech", "🔌"),
    ("Samsung", "samsung", "High-Tech", "📱"),
    ("Apple", "apple", "High-Tech", "🍎"),
    ("Dell", "dell", "High-Tech", "💻"),
    ("Lenovo", "lenovo", "High-Tech", "🖥️"),
    
    # Mode
    ("SHEIN", "shein", "Mode", "👗"),
    ("Zalando", "zalando", "Mode", "👟"),
    ("ASOS", "asos", "Mode", "👕"),
    ("La Redoute", "la-redoute", "Mode", "🏠"),
    ("Showroomprivé", "showroomprive", "Mode", "🛍️"),
    ("Veepee", "veepee", "Mode", "⚡"),
    
    # Sport
    ("Nike", "nike", "Sport", "✔️"),
    ("Adidas", "adidas", "Sport", "⚽"),
    ("Decathlon", "decathlon", "Sport", "🚴"),
    
    # Beauté
    ("Sephora", "sephora", "Beauté", "💄"),
    ("Nocibé", "nocibe", "Beauté", "💅"),
    ("Yves Rocher", "yves-rocher", "Beauté", "🌿"),
    
    # Voyage
    ("Booking", "booking", "Voyage", "🏨"),
    ("Expedia", "expedia", "Voyage", "✈️"),
    ("Hotels.com", "hotels-com", "Voyage", "🛏️"),
    
    # Food
    ("Uber Eats", "uber-eats", "Food", "🍔"),
    
    # Maison
    ("Leroy Merlin", "leroy-merlin", "Maison", "🔨"),
    ("IKEA", "ikea", "Maison", "🪑"),
    ("Dyson", "dyson", "Maison", "🌀"),
]


class CashbackScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.results = {}
        self.errors = []
    
    def extract_rate(self, text):
        """Extrait le taux numérique depuis du texte"""
        if not text:
            return 0.0
        
        text = text.lower().replace(',', '.').strip()
        
        patterns = [
            r'jusqu[\'"\s]*[àa]\s*(\d+(?:\.\d+)?)\s*%',
            r'(\d+(?:\.\d+)?)\s*%\s*(?:de\s+)?(?:cashback|remboursé)',
            r'(\d+(?:\.\d+)?)\s*%',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return float(match.group(1))
        
        return 0.0
    
    def scrape_igraal(self, slug):
        """Scrape iGraal"""
        urls = [
            f"https://fr.igraal.com/codes-promo/{slug}",
            f"https://fr.igraal.com/{slug}",
        ]
        
        for url in urls:
            try:
                resp = self.session.get(url, timeout=15, allow_redirects=True)
                if resp.status_code != 200:
                    continue
                
                soup = BeautifulSoup(resp.text, 'html.parser')
                
                # Meta description
                meta = soup.find('meta', {'name': 'description'})
                if meta:
                    content = meta.get('content', '')
                    rate = self.extract_rate(content)
                    if rate > 0:
                        return {'platform': 'iGraal', 'rate': rate, 'url': url}
                
                # Titre
                title = soup.find('title')
                if title:
                    rate = self.extract_rate(title.get_text())
                    if rate > 0:
                        return {'platform': 'iGraal', 'rate': rate, 'url': url}
                
            except Exception as e:
                self.errors.append(f"iGraal/{slug}: {e}")
        
        return None
    
    def scrape_widilo(self, slug):
        """Scrape Widilo"""
        urls = [
            f"https://www.widilo.fr/code-promo/{slug}",
            f"https://www.widilo.fr/{slug}",
        ]
        
        for url in urls:
            try:
                resp = self.session.get(url, timeout=15, allow_redirects=True)
                if resp.status_code != 200:
                    continue
                
                soup = BeautifulSoup(resp.text, 'html.parser')
                
                meta = soup.find('meta', {'name': 'description'})
                if meta:
                    content = meta.get('content', '')
                    rate = self.extract_rate(content)
                    if rate > 0:
                        return {'platform': 'Widilo', 'rate': rate, 'url': url}
                
                title = soup.find('title')
                if title:
                    rate = self.extract_rate(title.get_text())
                    if rate > 0:
                        return {'platform': 'Widilo', 'rate': rate, 'url': url}
                
            except Exception as e:
                self.errors.append(f"Widilo/{slug}: {e}")
        
        return None
    
    def scrape_poulpeo(self, slug):
        """Scrape Poulpeo"""
        urls = [
            f"https://www.poulpeo.com/cashback/{slug}",
            f"https://www.poulpeo.com/{slug}",
        ]
        
        for url in urls:
            try:
                resp = self.session.get(url, timeout=15, allow_redirects=True)
                if resp.status_code != 200:
                    continue
                
                soup = BeautifulSoup(resp.text, 'html.parser')
                
                meta = soup.find('meta', {'name': 'description'})
                if meta:
                    content = meta.get('content', '')
                    rate = self.extract_rate(content)
                    if rate > 0:
                        return {'platform': 'Poulpeo', 'rate': rate, 'url': url}
                
                title = soup.find('title')
                if title:
                    rate = self.extract_rate(title.get_text())
                    if rate > 0:
                        return {'platform': 'Poulpeo', 'rate': rate, 'url': url}
                
            except Exception as e:
                self.errors.append(f"Poulpeo/{slug}: {e}")
        
        return None
    
    def scrape_ebuyclub(self, slug):
        """Scrape eBuyClub"""
        urls = [
            f"https://www.ebuyclub.com/reduction-{slug}",
            f"https://www.ebuyclub.com/cashback/{slug}",
        ]
        
        for url in urls:
            try:
                resp = self.session.get(url, timeout=15, allow_redirects=True)
                if resp.status_code != 200:
                    continue
                
                soup = BeautifulSoup(resp.text, 'html.parser')
                
                meta = soup.find('meta', {'name': 'description'})
                if meta:
                    content = meta.get('content', '')
                    rate = self.extract_rate(content)
                    if rate > 0:
                        return {'platform': 'eBuyClub', 'rate': rate, 'url': url}
                
                title = soup.find('title')
                if title:
                    rate = self.extract_rate(title.get_text())
                    if rate > 0:
                        return {'platform': 'eBuyClub', 'rate': rate, 'url': url}
                
            except Exception as e:
                self.errors.append(f"eBuyClub/{slug}: {e}")
        
        return None
    
    def scrape_merchant(self, name, slug, category, emoji):
        """Scrape un marchand sur toutes les plateformes"""
        print(f"🔍 {name}...", end=" ", flush=True)
        
        rates = []
        
        scrapers = [
            self.scrape_igraal,
            self.scrape_widilo,
            self.scrape_poulpeo,
            self.scrape_ebuyclub,
        ]
        
        for scraper in scrapers:
            result = scraper(slug)
            if result:
                rates.append(result)
            time.sleep(random.uniform(0.3, 0.8))
        
        best_rate = 0
        best_platform = None
        if rates:
            best = max(rates, key=lambda x: x['rate'])
            best_rate = best['rate']
            best_platform = best['platform']
        
        print(f"✅ {len(rates)} plateformes, best: {best_rate}%")
        
        return {
            'name': name,
            'slug': slug,
            'category': category,
            'logo': emoji,
            'rates': rates,
            'best_rate': best_rate,
            'best_platform': best_platform,
        }
    
    def run(self):
        """Lance le scraping complet"""
        print(f"🚀 CASHBACKITO - Scraping démarré")
        print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print(f"📦 {len(MERCHANTS)} marchands à scraper\n")
        
        merchants_data = []
        
        for name, slug, category, emoji in MERCHANTS:
            data = self.scrape_merchant(name, slug, category, emoji)
            if data['rates']:
                merchants_data.append(data)
            time.sleep(random.uniform(0.5, 1.0))
        
        total_rates = sum(len(m['rates']) for m in merchants_data)
        print(f"\n✨ Terminé!")
        print(f"   📊 {len(merchants_data)} marchands avec données")
        print(f"   📈 {total_rates} taux récupérés")
        print(f"   ⚠️  {len(self.errors)} erreurs")
        
        return {
            'last_updated': datetime.now().isoformat(),
            'last_updated_fr': datetime.now().strftime('%d/%m/%Y à %Hh%M'),
            'stats': {
                'merchants_count': len(merchants_data),
                'rates_count': total_rates,
                'errors_count': len(self.errors),
            },
            'merchants': merchants_data,
        }
    
    def save(self, data, path='data/cashback_rates.json'):
        """Sauvegarde les données en JSON"""
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"💾 Sauvegardé: {path}")


if __name__ == '__main__':
    scraper = CashbackScraper()
    data = scraper.run()
    scraper.save(data)
