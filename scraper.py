#!/usr/bin/env python3
"""
Cashbackito Scraper V3
Scrape les taux de cashback depuis Poulpeo, Widilo, eBuyClub
Fix: ne capture que les vrais taux de cashback, pas les codes promo
"""

import requests
from bs4 import BeautifulSoup
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path

# Configuration des marchands
MERCHANTS = [
    # (Nom, slug_poulpeo, slug_widilo, slug_igraal, id_ebuyclub, categorie, emoji)
    ("AliExpress", "aliexpress", "aliexpress", "aliexpress", 6325, "Marketplace", "🛒"),
    ("Cdiscount", "cdiscount", "cdiscount", "cdiscount", 104, "Marketplace", "🏷️"),
    ("Rakuten", "rakuten", "rakuten", "rakuten", None, "Marketplace", "🛍️"),
    
    ("Fnac", "fnac", "fnac", "fnac", 58, "High-Tech", "🎮"),
    ("Darty", "darty", "darty", "darty", 846, "High-Tech", "📺"),
    ("Boulanger", "boulanger", "boulanger", "boulanger", 993, "High-Tech", "🔌"),
    ("Samsung", "samsung", "samsung", "samsung", None, "High-Tech", "📱"),
    
    ("ASOS", "asos", "asos", "asos", 3419, "Mode", "👕"),
    ("SHEIN", "shein", "shein", "shein", 7494, "Mode", "👗"),
    ("Zalando", "zalando", "zalando", "zalando", 3601, "Mode", "👠"),
    ("La Redoute", "la-redoute", "la-redoute", "la-redoute", None, "Mode", "🏠"),
    ("Showroomprive", "showroomprive", "showroomprive", "showroomprive", None, "Mode", "🛍️"),
    
    ("Nike", "nike", "nike", "nike", 1145, "Sport", "✔️"),
    ("Adidas", "adidas", "adidas", "adidas", 1356, "Sport", "⚽"),
    ("Decathlon", "decathlon", "decathlon", "decathlon", 880, "Sport", "🏃"),
    
    ("Sephora", "sephora", "sephora", "sephora", 683, "Beaute", "💄"),
    ("Nocibe", "nocibe", "nocibe", "nocibe", None, "Beaute", "💅"),
    ("Yves Rocher", "yves-rocher", "yves-rocher", "yves-rocher", None, "Beaute", "🌿"),
    
    ("Booking", "booking", "booking-com", "booking-com", 972, "Voyage", "🏨"),
    ("Expedia", "expedia", "expedia", "expedia", 487, "Voyage", "✈️"),
    
    ("IKEA", "ikea", "ikea", "ikea", 6214, "Maison", "🪑"),
    ("Maisons du Monde", "maisons-du-monde", "maisons-du-monde", "maisons-du-monde", None, "Maison", "🏡"),
    
    ("Uber Eats", "uber-eats", "uber-eats", "uber-eats", None, "Food", "🍔"),
]

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
}


def extract_cashback_rate(text):
    """
    Extrait UNIQUEMENT un taux de cashback explicite
    Pattern: "X% de cashback" ou "X% cashback" ou "cashback X%"
    Ignore les codes promo et réductions
    """
    if not text:
        return None
    
    text = text.lower().replace(',', '.')
    
    # Patterns spécifiques pour le cashback uniquement
    patterns = [
        r'(\d+(?:\.\d+)?)\s*%\s*(?:de\s+)?cashback',  # "3.6% de cashback" ou "3.6% cashback"
        r'cashback\s*(?:de\s+)?(\d+(?:\.\d+)?)\s*%',  # "cashback de 3.6%" ou "cashback 3.6%"
        r'jusqu.{0,3}(\d+(?:\.\d+)?)\s*%\s*(?:de\s+)?cashback',  # "jusqu'à 3.6% de cashback"
        r'(\d+(?:\.\d+)?)\s*%\s*rembours',  # "3.6% remboursés"
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            rate = float(match.group(1))
            # Filtre les taux aberrants (cashback > 20% c'est suspect)
            if 0 < rate <= 20:
                return rate
    
    return None


class CashbackScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        
    def scrape_poulpeo(self, slug):
        """Scrape Poulpeo - cherche le cashback dans meta/titre"""
        url = f"https://www.poulpeo.com/reductions-{slug}.htm"
        try:
            resp = self.session.get(url, timeout=15)
            if resp.status_code != 200:
                return None
            
            soup = BeautifulSoup(resp.text, 'lxml')
            
            # Meta description - source la plus fiable
            meta = soup.find('meta', {'name': 'description'})
            if meta:
                content = meta.get('content', '')
                rate = extract_cashback_rate(content)
                if rate:
                    return rate
            
            # Titre en fallback
            title = soup.find('title')
            if title:
                rate = extract_cashback_rate(title.get_text())
                if rate:
                    return rate
            
            return None
        except Exception as e:
            return None
    
    def scrape_widilo(self, slug):
        """Scrape Widilo - cherche UNIQUEMENT 'X% de cashback' dans la meta"""
        url = f"https://www.widilo.fr/code-promo/{slug}"
        try:
            resp = self.session.get(url, timeout=15)
            if resp.status_code != 200:
                return None
            
            soup = BeautifulSoup(resp.text, 'lxml')
            
            # Meta description - seule source fiable pour Widilo
            # La meta contient "X% de cashback" si le marchand a du cashback
            meta = soup.find('meta', {'name': 'description'})
            if meta:
                content = meta.get('content', '')
                rate = extract_cashback_rate(content)
                if rate:
                    return rate
            
            # Titre en fallback (mais moins fiable)
            title = soup.find('title')
            if title:
                rate = extract_cashback_rate(title.get_text())
                if rate:
                    return rate
            
            # NE PAS chercher dans les éléments HTML - trop de faux positifs
            return None
            
        except Exception as e:
            return None
    
    def scrape_ebuyclub(self, slug, merchant_id):
        """Scrape eBuyClub - cherche 'X% Cashback' dans titre/meta"""
        if not merchant_id:
            return None
        
        url = f"https://www.ebuyclub.com/reduction-{slug}-{merchant_id}"
        try:
            resp = self.session.get(url, timeout=15, allow_redirects=True)
            if resp.status_code != 200:
                return None
            
            soup = BeautifulSoup(resp.text, 'lxml')
            
            # Titre - pattern "X% Cashback"
            title = soup.find('title')
            if title:
                title_text = title.get_text()
                # eBuyClub format: "... + X% Cashback" ou "... + X,X% Cashback"
                match = re.search(r'(\d+(?:[,.]\d+)?)\s*%\s*[Cc]ash[Bb]ack', title_text)
                if match:
                    rate = float(match.group(1).replace(',', '.'))
                    if 0 < rate <= 20:
                        return rate
            
            return None
            
        except Exception as e:
            return None
    
    def scrape_merchant(self, merchant_data):
        """Scrape toutes les plateformes pour un marchand"""
        name, slug_p, slug_w, slug_i, id_eb, category, emoji = merchant_data
        
        print(f"{emoji} {name}...", end=" ")
        
        rates = []
        
        # Poulpeo
        rate = self.scrape_poulpeo(slug_p)
        if rate:
            rates.append({
                "platform": "Poulpeo",
                "rate": rate,
                "url": f"https://www.poulpeo.com/reductions-{slug_p}.htm"
            })
        time.sleep(0.3)
        
        # Widilo
        rate = self.scrape_widilo(slug_w)
        if rate:
            rates.append({
                "platform": "Widilo",
                "rate": rate,
                "url": f"https://www.widilo.fr/code-promo/{slug_w}"
            })
        time.sleep(0.3)
        
        # eBuyClub
        if id_eb:
            rate = self.scrape_ebuyclub(slug_p, id_eb)
            if rate:
                rates.append({
                    "platform": "eBuyClub",
                    "rate": rate,
                    "url": f"https://www.ebuyclub.com/reduction-{slug_p}-{id_eb}"
                })
            time.sleep(0.3)
        
        if rates:
            best = max(rates, key=lambda x: x['rate'])
            print(f"OK ({len(rates)} taux, best: {best['rate']}% sur {best['platform']})")
            return {
                "name": name,
                "slug": slug_p,
                "category": category,
                "logo": emoji,
                "rates": rates,
                "best_rate": best['rate'],
                "best_platform": best['platform']
            }
        else:
            print("AUCUN CASHBACK")
            return None
    
    def run(self):
        """Lance le scraping complet"""
        print("=" * 60)
        print("CASHBACKITO SCRAPER V3")
        print("=" * 60)
        print(f"Date: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        print(f"Marchands: {len(MERCHANTS)}")
        print("-" * 60)
        
        merchants_data = []
        no_cashback = []
        
        for merchant in MERCHANTS:
            result = self.scrape_merchant(merchant)
            if result:
                merchants_data.append(result)
            else:
                no_cashback.append(merchant[0])
        
        total_rates = sum(len(m.get('rates', [])) for m in merchants_data)
        
        output = {
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "last_updated_fr": datetime.now().strftime('%d/%m/%Y a %Hh%M'),
            "stats": {
                "merchants_count": len(merchants_data),
                "rates_count": total_rates,
                "no_cashback_count": len(no_cashback)
            },
            "merchants": merchants_data
        }
        
        # Sauvegarder
        output_dir = Path(__file__).parent / "data"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "cashback_rates.json"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        
        print("-" * 60)
        print("RESULTATS")
        print("-" * 60)
        print(f"Marchands avec cashback: {len(merchants_data)}")
        print(f"Total taux: {total_rates}")
        
        if no_cashback:
            print(f"Sans cashback: {', '.join(no_cashback)}")
        
        # Stats par plateforme
        platform_counts = {}
        for m in merchants_data:
            for r in m.get('rates', []):
                p = r['platform']
                platform_counts[p] = platform_counts.get(p, 0) + 1
        
        print(f"\nPar plateforme:")
        for p, c in sorted(platform_counts.items(), key=lambda x: -x[1]):
            print(f"  {p}: {c}")
        
        print(f"\nFichier: {output_path}")
        
        return output


if __name__ == "__main__":
    scraper = CashbackScraper()
    scraper.run()
