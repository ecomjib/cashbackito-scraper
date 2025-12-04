#!/usr/bin/env python3
"""
Cashbackito Scraper V2.1 - DEBUG VERSION
Scrape les taux de cashback depuis Poulpeo, Widilo, iGraal, eBuyClub
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

# Mode debug - affiche plus d'infos
DEBUG = True


def extract_rate(text):
    """Extrait un taux numerique depuis un texte"""
    if not text:
        return None
    text = text.replace(',', '.').replace(' ', '')
    match = re.search(r'(\d+(?:\.\d+)?)\s*%', text)
    if match:
        try:
            rate = float(match.group(1))
            if rate < 50:  # Filtre taux aberrants
                return rate
        except:
            pass
    return None


class CashbackScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        
    def scrape_poulpeo(self, slug):
        """Scrape Poulpeo - URL: poulpeo.com/reductions-{slug}.htm"""
        url = f"https://www.poulpeo.com/reductions-{slug}.htm"
        try:
            resp = self.session.get(url, timeout=15)
            if DEBUG:
                print(f"    [Poulpeo] Status: {resp.status_code}")
            if resp.status_code != 200:
                return None
            
            soup = BeautifulSoup(resp.text, 'lxml')
            
            # Meta description
            meta = soup.find('meta', {'name': 'description'})
            if meta:
                content = meta.get('content', '')
                if DEBUG:
                    print(f"    [Poulpeo] Meta: {content[:100]}...")
                rate = extract_rate(content)
                if rate:
                    return rate
            
            # Titre
            title = soup.find('title')
            if title:
                title_text = title.get_text()
                if DEBUG:
                    print(f"    [Poulpeo] Title: {title_text[:80]}...")
                rate = extract_rate(title_text)
                if rate:
                    return rate
            
            return None
        except Exception as e:
            if DEBUG:
                print(f"    [Poulpeo] Error: {e}")
            return None
    
    def scrape_widilo(self, slug):
        """Scrape Widilo - URL: widilo.fr/code-promo/{slug}"""
        url = f"https://www.widilo.fr/code-promo/{slug}"
        try:
            resp = self.session.get(url, timeout=15)
            if DEBUG:
                print(f"    [Widilo] Status: {resp.status_code}, URL: {resp.url}")
            if resp.status_code != 200:
                return None
            
            soup = BeautifulSoup(resp.text, 'lxml')
            
            # Titre
            title = soup.find('title')
            if title:
                title_text = title.get_text()
                if DEBUG:
                    print(f"    [Widilo] Title: {title_text[:100]}...")
                # Pattern plus flexible
                patterns = [
                    r'(\d+(?:[,.]\d+)?)\s*%\s*(?:de\s+)?cashback',
                    r'cashback\s*[:\-]?\s*(\d+(?:[,.]\d+)?)\s*%',
                    r'(\d+(?:[,.]\d+)?)\s*%\s*rembours',
                ]
                for pattern in patterns:
                    match = re.search(pattern, title_text, re.IGNORECASE)
                    if match:
                        rate = float(match.group(1).replace(',', '.'))
                        if rate < 50:
                            return rate
            
            # Meta description
            meta = soup.find('meta', {'name': 'description'})
            if meta:
                content = meta.get('content', '')
                if DEBUG:
                    print(f"    [Widilo] Meta: {content[:100]}...")
                for pattern in [r'(\d+(?:[,.]\d+)?)\s*%\s*(?:de\s+)?cashback', r'(\d+(?:[,.]\d+)?)\s*%']:
                    match = re.search(pattern, content, re.IGNORECASE)
                    if match:
                        rate = float(match.group(1).replace(',', '.'))
                        if rate < 50:
                            return rate
            
            # Chercher dans le body - classe contenant "cashback"
            cashback_elements = soup.find_all(class_=re.compile(r'cashback', re.IGNORECASE))
            for elem in cashback_elements[:3]:
                text = elem.get_text()
                if DEBUG and text.strip():
                    print(f"    [Widilo] Cashback elem: {text[:60]}...")
                rate = extract_rate(text)
                if rate:
                    return rate
            
            return None
        except Exception as e:
            if DEBUG:
                print(f"    [Widilo] Error: {e}")
            return None
    
    def scrape_igraal(self, slug):
        """Scrape iGraal - URL: fr.igraal.com/codes-promo/{slug}"""
        url = f"https://fr.igraal.com/codes-promo/{slug}"
        try:
            resp = self.session.get(url, timeout=15)
            if DEBUG:
                print(f"    [iGraal] Status: {resp.status_code}, URL: {resp.url}")
            if resp.status_code != 200:
                return None
            
            soup = BeautifulSoup(resp.text, 'lxml')
            
            # Titre
            title = soup.find('title')
            if title:
                title_text = title.get_text()
                if DEBUG:
                    print(f"    [iGraal] Title: {title_text[:100]}...")
                patterns = [
                    r'(\d+(?:[,.]\d+)?)\s*%\s*(?:de\s+)?cashback',
                    r'cashback\s*(\d+(?:[,.]\d+)?)\s*%',
                    r'(\d+(?:[,.]\d+)?)\s*%\s*rembours',
                ]
                for pattern in patterns:
                    match = re.search(pattern, title_text, re.IGNORECASE)
                    if match:
                        rate = float(match.group(1).replace(',', '.'))
                        if rate < 50:
                            return rate
            
            # Meta description
            meta = soup.find('meta', {'name': 'description'})
            if meta:
                content = meta.get('content', '')
                if DEBUG:
                    print(f"    [iGraal] Meta: {content[:100]}...")
                for pattern in [r'(\d+(?:[,.]\d+)?)\s*%\s*(?:de\s+)?cashback', r'(\d+(?:[,.]\d+)?)\s*%']:
                    match = re.search(pattern, content, re.IGNORECASE)
                    if match:
                        rate = float(match.group(1).replace(',', '.'))
                        if rate < 50:
                            return rate
            
            # Chercher le taux dans des balises specifiques
            # iGraal affiche souvent "Jusqu'à X% de cashback"
            page_text = soup.get_text()
            match = re.search(r"jusqu.{0,3}[aà]\s*(\d+(?:[,.]\d+)?)\s*%", page_text, re.IGNORECASE)
            if match:
                rate = float(match.group(1).replace(',', '.'))
                if DEBUG:
                    print(f"    [iGraal] Found 'jusqu'à': {rate}%")
                if rate < 50:
                    return rate
            
            return None
        except Exception as e:
            if DEBUG:
                print(f"    [iGraal] Error: {e}")
            return None
    
    def scrape_ebuyclub(self, slug, merchant_id):
        """Scrape eBuyClub - URL: ebuyclub.com/reduction-{slug}-{id}"""
        if not merchant_id:
            return None
        
        # Construire l'URL correcte avec le slug
        url = f"https://www.ebuyclub.com/reduction-{slug}-{merchant_id}"
        try:
            resp = self.session.get(url, timeout=15, allow_redirects=True)
            if DEBUG:
                print(f"    [eBuyClub] Status: {resp.status_code}, Final URL: {resp.url}")
            
            if resp.status_code != 200:
                return None
            
            soup = BeautifulSoup(resp.text, 'lxml')
            
            # Titre - pattern: "X% Cashback" ou "X% en CashBack"
            title = soup.find('title')
            if title:
                title_text = title.get_text()
                if DEBUG:
                    print(f"    [eBuyClub] Title: {title_text[:100]}...")
                patterns = [
                    r'(\d+(?:[,.]\d+)?)\s*%\s*(?:en\s+)?[Cc]ash[Bb]ack',
                    r'(\d+(?:[,.]\d+)?)\s*%\s*rembours',
                    r'[Cc]ash[Bb]ack\s*[:\-]?\s*(\d+(?:[,.]\d+)?)\s*%',
                ]
                for pattern in patterns:
                    match = re.search(pattern, title_text)
                    if match:
                        rate = float(match.group(1).replace(',', '.'))
                        if rate < 50:
                            return rate
            
            # Meta description
            meta = soup.find('meta', {'name': 'description'})
            if meta:
                content = meta.get('content', '')
                if DEBUG:
                    print(f"    [eBuyClub] Meta: {content[:100]}...")
                match = re.search(r'(\d+(?:[,.]\d+)?)\s*%\s*(?:en\s+)?[Cc]ash[Bb]ack', content)
                if match:
                    rate = float(match.group(1).replace(',', '.'))
                    if rate < 50:
                        return rate
            
            return None
        except Exception as e:
            if DEBUG:
                print(f"    [eBuyClub] Error: {e}")
            return None
    
    def scrape_merchant(self, merchant_data):
        """Scrape toutes les plateformes pour un marchand"""
        name, slug_p, slug_w, slug_i, id_eb, category, emoji = merchant_data
        
        print(f"\n{emoji} {name}")
        print("-" * 40)
        
        rates = []
        
        # Poulpeo
        print("  Poulpeo:")
        rate = self.scrape_poulpeo(slug_p)
        if rate:
            rates.append({"platform": "Poulpeo", "rate": rate, "url": f"https://www.poulpeo.com/reductions-{slug_p}.htm"})
            print(f"    => {rate}%")
        else:
            print(f"    => AUCUN")
        time.sleep(0.5)
        
        # Widilo
        print("  Widilo:")
        rate = self.scrape_widilo(slug_w)
        if rate:
            rates.append({"platform": "Widilo", "rate": rate, "url": f"https://www.widilo.fr/code-promo/{slug_w}"})
            print(f"    => {rate}%")
        else:
            print(f"    => AUCUN")
        time.sleep(0.5)
        
        # iGraal
        print("  iGraal:")
        rate = self.scrape_igraal(slug_i)
        if rate:
            rates.append({"platform": "iGraal", "rate": rate, "url": f"https://fr.igraal.com/codes-promo/{slug_i}"})
            print(f"    => {rate}%")
        else:
            print(f"    => AUCUN")
        time.sleep(0.5)
        
        # eBuyClub
        if id_eb:
            print("  eBuyClub:")
            rate = self.scrape_ebuyclub(slug_p, id_eb)  # Utilise slug_p comme base
            if rate:
                rates.append({"platform": "eBuyClub", "rate": rate, "url": f"https://www.ebuyclub.com/reduction-{slug_p}-{id_eb}"})
                print(f"    => {rate}%")
            else:
                print(f"    => AUCUN")
            time.sleep(0.5)
        
        if rates:
            best = max(rates, key=lambda x: x['rate'])
            print(f"  BEST: {best['rate']}% sur {best['platform']}")
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
            print(f"  AUCUN TAUX TROUVE")
            return None
    
    def run(self):
        """Lance le scraping complet"""
        print("=" * 60)
        print("CASHBACKITO SCRAPER V2.1 - DEBUG")
        print("=" * 60)
        print(f"Date: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        print(f"Marchands: {len(MERCHANTS)}")
        print(f"Debug: {'ON' if DEBUG else 'OFF'}")
        
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
            "last_updated": datetime.now(timezone.utc).isoformat(),
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
        
        print("\n" + "=" * 60)
        print("RESULTATS FINAUX")
        print("=" * 60)
        print(f"Marchands avec taux: {len(merchants_data)}/{len(MERCHANTS)}")
        print(f"Total taux recuperes: {total_rates}")
        print(f"Erreurs (0 taux): {errors}")
        print(f"Fichier: {output_path}")
        
        # Stats par plateforme
        platform_counts = {}
        for m in merchants_data:
            for r in m.get('rates', []):
                p = r['platform']
                platform_counts[p] = platform_counts.get(p, 0) + 1
        
        print("\nTaux par plateforme:")
        for p, c in sorted(platform_counts.items(), key=lambda x: -x[1]):
            print(f"  {p}: {c}")
        
        return output


if __name__ == "__main__":
    scraper = CashbackScraper()
    scraper.run()
