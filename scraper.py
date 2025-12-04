#!/usr/bin/env python3
"""
Cashbackito Scraper V2
Scrape les taux de cashback depuis Poulpeo, Widilo, iGraal, eBuyClub
"""

import requests
from bs4 import BeautifulSoup
import json
import re
import time
from datetime import datetime
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
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.7',
}


def extract_rate(text):
    """Extrait un taux numerique depuis un texte"""
    if not text:
        return None
    text = text.replace(',', '.').replace(' ', '')
    match = re.search(r'(\d+(?:\.\d+)?)\s*%', text)
    if match:
        try:
            return float(match.group(1))
        except:
            pass
    return None


class CashbackScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        
    def scrape_poulpeo(self, slug):
        """Scrape Poulpeo"""
        url = f"https://www.poulpeo.com/reductions-{slug}.htm"
        try:
            resp = self.session.get(url, timeout=15)
            if resp.status_code != 200:
                return None
            
            soup = BeautifulSoup(resp.text, 'lxml')
            
            # Meta description
            meta = soup.find('meta', {'name': 'description'})
            if meta:
                rate = extract_rate(meta.get('content', ''))
                if rate and rate < 50:  # Filtre taux aberrants
                    return rate
            
            # Titre
            title = soup.find('title')
            if title:
                rate = extract_rate(title.get_text())
                if rate and rate < 50:
                    return rate
            
            # Pattern cashback dans le texte
            text = soup.get_text()
            match = re.search(r'(\d+(?:[,.]\d+)?)\s*%\s*(?:de\s+)?(?:cashback|rembours)', text, re.IGNORECASE)
            if match:
                rate = float(match.group(1).replace(',', '.'))
                if rate < 50:
                    return rate
            
            return None
        except Exception as e:
            return None
    
    def scrape_widilo(self, slug):
        """Scrape Widilo"""
        url = f"https://www.widilo.fr/code-promo/{slug}"
        try:
            resp = self.session.get(url, timeout=15)
            if resp.status_code != 200:
                return None
            
            soup = BeautifulSoup(resp.text, 'lxml')
            
            # Titre
            title = soup.find('title')
            if title:
                match = re.search(r'(\d+(?:[,.]\d+)?)\s*%\s*(?:de\s+)?cashback', title.get_text(), re.IGNORECASE)
                if match:
                    rate = float(match.group(1).replace(',', '.'))
                    if rate < 50:
                        return rate
            
            # Meta
            meta = soup.find('meta', {'name': 'description'})
            if meta:
                match = re.search(r'(\d+(?:[,.]\d+)?)\s*%\s*(?:de\s+)?cashback', meta.get('content', ''), re.IGNORECASE)
                if match:
                    rate = float(match.group(1).replace(',', '.'))
                    if rate < 50:
                        return rate
            
            return None
        except Exception as e:
            return None
    
    def scrape_igraal(self, slug):
        """Scrape iGraal"""
        url = f"https://fr.igraal.com/codes-promo/{slug}"
        try:
            resp = self.session.get(url, timeout=15)
            if resp.status_code != 200:
                return None
            
            soup = BeautifulSoup(resp.text, 'lxml')
            
            # Titre
            title = soup.find('title')
            if title:
                match = re.search(r'(\d+(?:[,.]\d+)?)\s*%\s*(?:de\s+)?cashback', title.get_text(), re.IGNORECASE)
                if match:
                    rate = float(match.group(1).replace(',', '.'))
                    if rate < 50:
                        return rate
            
            # Meta
            meta = soup.find('meta', {'name': 'description'})
            if meta:
                match = re.search(r'(\d+(?:[,.]\d+)?)\s*%\s*(?:de\s+)?cashback', meta.get('content', ''), re.IGNORECASE)
                if match:
                    rate = float(match.group(1).replace(',', '.'))
                    if rate < 50:
                        return rate
            
            return None
        except Exception as e:
            return None
    
    def scrape_ebuyclub(self, merchant_id):
        """Scrape eBuyClub"""
        if not merchant_id:
            return None
        
        try:
            url = f"https://www.ebuyclub.com/avis/-{merchant_id}"
            resp = self.session.get(url, timeout=15, allow_redirects=True)
            
            soup = BeautifulSoup(resp.text, 'lxml')
            
            title = soup.find('title')
            if title:
                match = re.search(r'(\d+(?:[,.]\d+)?)\s*%\s*(?:en\s+)?[Cc]ash[Bb]ack', title.get_text())
                if match:
                    rate = float(match.group(1).replace(',', '.'))
                    if rate < 50:
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
            rates.append({"platform": "Poulpeo", "rate": rate, "url": f"https://www.poulpeo.com/reductions-{slug_p}.htm"})
        time.sleep(0.3)
        
        # Widilo
        rate = self.scrape_widilo(slug_w)
        if rate:
            rates.append({"platform": "Widilo", "rate": rate, "url": f"https://www.widilo.fr/code-promo/{slug_w}"})
        time.sleep(0.3)
        
        # iGraal
        rate = self.scrape_igraal(slug_i)
        if rate:
            rates.append({"platform": "iGraal", "rate": rate, "url": f"https://fr.igraal.com/codes-promo/{slug_i}"})
        time.sleep(0.3)
        
        # eBuyClub
        if id_eb:
            rate = self.scrape_ebuyclub(id_eb)
            if rate:
                rates.append({"platform": "eBuyClub", "rate": rate, "url": f"https://www.ebuyclub.com"})
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
            print("AUCUN")
            return None
    
    def run(self):
        """Lance le scraping complet"""
        print("=" * 60)
        print("CASHBACKITO SCRAPER V2")
        print("=" * 60)
        print(f"Date: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        print(f"Marchands: {len(MERCHANTS)}")
        print("-" * 60)
        
        merchants_data = []
        errors = 0
        
        for merchant in MERCHANTS:
            result = self.scrape_merchant(merchant)
            if result:
                merchants_data.append(result)
            else:
                errors += 1
        
        total_rates = sum(len(m.get('rates', [])) for m in merchants_data)
        
        output = {
            "last_updated": datetime.utcnow().isoformat(),
            "last_updated_fr": datetime.now().strftime('%d/%m/%Y a %Hh%M'),
            "stats": {
                "merchants_count": len(merchants_data),
                "rates_count": total_rates,
                "errors_count": errors
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
        print(f"RESULTATS: {len(merchants_data)} marchands, {total_rates} taux, {errors} erreurs")
        print(f"Fichier: {output_path}")
        
        return output


if __name__ == "__main__":
    scraper = CashbackScraper()
    scraper.run()
