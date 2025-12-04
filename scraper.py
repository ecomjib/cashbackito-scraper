#!/usr/bin/env python3
"""
Cashbackito Scraper V5
- Patterns corrigés basés sur l'analyse debug
- IDs eBuyClub nettoyés (seuls les IDs valides)
- Détection cashback + bons d'achat
- iGraal abandonné (403 systématique)
"""

import requests
from bs4 import BeautifulSoup
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path

# Configuration des marchands
# Format: (Nom, slug_poulpeo, slug_widilo, id_ebuyclub, categorie, emoji)
# id_ebuyclub = None si pas de page valide
MERCHANTS = [
    # Marketplace
    ("AliExpress", "aliexpress", "aliexpress", 6325, "Marketplace", "🛒"),
    ("Cdiscount", "cdiscount", "cdiscount", 104, "Marketplace", "🏷️"),
    ("Rakuten", None, "rakuten", None, "Marketplace", "🛍️"),  # Poulpeo = Rakuten TV, pas bon
    
    # High-Tech
    ("Fnac", "fnac", "fnac", 58, "High-Tech", "🎮"),
    ("Darty", "darty", "darty", 846, "High-Tech", "📺"),
    ("Boulanger", "boulanger", "boulanger", None, "High-Tech", "🔌"),  # Pas de cashback
    ("Samsung", "samsung", "samsung", None, "High-Tech", "📱"),  # eBuyClub ID faux
    
    # Mode
    ("ASOS", "asos", "asos", 3419, "Mode", "👕"),
    ("SHEIN", "shein", "shein", 7494, "Mode", "👗"),
    ("Zalando", "zalando", "zalando", None, "Mode", "👠"),  # Bon d'achat seulement
    ("La Redoute", "la-redoute", "la-redoute", None, "Mode", "🏠"),  # eBuyClub ID faux
    ("Showroomprive", "showroomprive", "showroomprive", None, "Mode", "🛍️"),  # eBuyClub ID faux
    
    # Sport
    ("Nike", "nike", "nike", 1145, "Sport", "✔️"),
    ("Adidas", "adidas", "adidas", 1356, "Sport", "⚽"),
    ("Decathlon", "decathlon", "decathlon", None, "Sport", "🏃"),  # Pas de cashback
    
    # Beauté
    ("Sephora", "sephora", "sephora", 683, "Beaute", "💄"),
    ("Nocibe", "nocibe", "nocibe", None, "Beaute", "💅"),  # eBuyClub erreur 500
    ("Yves Rocher", "yves-rocher", "yves-rocher", None, "Beaute", "🌿"),  # eBuyClub ID faux
    
    # Voyage
    ("Booking", "booking", "booking", None, "Voyage", "🏨"),  # Widilo = booking (pas booking-com)
    ("Expedia", "expedia", "expedia", 487, "Voyage", "✈️"),
    
    # Maison
    ("IKEA", "ikea", "ikea", None, "Maison", "🪑"),  # Pas de cashback
    ("Maisons du Monde", None, "maisons-du-monde", None, "Maison", "🏡"),  # Poulpeo = Becquet
    
    # Food
    ("Uber Eats", None, "uber-eats", None, "Food", "🍔"),  # Poulpeo = Burger King
]

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
}


def extract_cashback_rate(text):
    """
    Extrait le taux de CASHBACK uniquement (pas codes promo)
    Patterns basés sur l'analyse des metas réelles
    """
    if not text:
        return None
    
    text_lower = text.lower().replace(',', '.')
    
    # Patterns très spécifiques pour éviter les faux positifs
    patterns = [
        r'jusqu.{0,5}(\d+(?:\.\d+)?)\s*%\s*(?:de\s+)?cashback',  # "jusqu'à 4,5% de cashback"
        r'(\d+(?:\.\d+)?)\s*%\s*(?:de\s+)?cashback',              # "3.6% de cashback"
        r'(\d+(?:\.\d+)?)\s*%\s*(?:en\s+)?cashback',              # "3.6% en cashback"
        r'(\d+(?:\.\d+)?)\s*%\s*rembours',                        # "2,25% remboursés"
        r'cashback\s*(?:de\s+)?(\d+(?:\.\d+)?)\s*%',              # "cashback de 3.6%"
        r'\+\s*(\d+(?:\.\d+)?)\s*%\s*cashback',                   # "+ 4,2% Cashback" (eBuyClub)
        r'cashback\s+(\d+(?:\.\d+)?)\s*%',                        # "Cashback 5%" (eBuyClub)
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text_lower)
        if match:
            rate = float(match.group(1))
            if 0.1 <= rate <= 20:  # Filtre taux réalistes
                return rate
    
    return None


def extract_bon_achat_rate(text):
    """
    Extrait le taux de BON D'ACHAT uniquement
    """
    if not text:
        return None
    
    text_lower = text.lower().replace(',', '.')
    
    patterns = [
        r'(\d+(?:\.\d+)?)\s*%\s*(?:en\s+)?bon\s*d.?achat',        # "14% en bon d'achat"
        r'bon\s*d.?achat\s*(?:de\s+)?(\d+(?:\.\d+)?)\s*%',        # "bon d'achat de 14%"
        r'(\d+(?:\.\d+)?)\s*%\s*(?:sur\s+)?(?:les?\s+)?bons?\s*d.?achats?',
        r'(\d+(?:\.\d+)?)\s*%\s*(?:en\s+)?carte\s*cadeau',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text_lower)
        if match:
            rate = float(match.group(1))
            if 0.1 <= rate <= 25:
                return rate
    
    return None


class CashbackScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        
    def get_page_meta(self, url):
        """Récupère le titre et la meta description d'une page"""
        try:
            resp = self.session.get(url, timeout=15, allow_redirects=True)
            if resp.status_code != 200:
                return None
            
            soup = BeautifulSoup(resp.text, 'lxml')
            
            title = ""
            title_tag = soup.find('title')
            if title_tag:
                title = title_tag.get_text()
            
            meta_desc = ""
            meta = soup.find('meta', {'name': 'description'})
            if meta:
                meta_desc = meta.get('content', '')
            
            return {'title': title, 'meta': meta_desc}
            
        except Exception:
            return None
    
    def scrape_poulpeo(self, slug):
        """Scrape Poulpeo"""
        if not slug:
            return None
            
        url = f"https://www.poulpeo.com/reductions-{slug}.htm"
        data = self.get_page_meta(url)
        if not data:
            return None
        
        combined = f"{data['title']} {data['meta']}"
        cashback = extract_cashback_rate(combined)
        bon_achat = extract_bon_achat_rate(combined)
        
        if cashback or bon_achat:
            return {'url': url, 'cashback': cashback, 'bon_achat': bon_achat}
        return None
    
    def scrape_widilo(self, slug):
        """Scrape Widilo"""
        if not slug:
            return None
            
        url = f"https://www.widilo.fr/code-promo/{slug}"
        data = self.get_page_meta(url)
        if not data:
            return None
        
        combined = f"{data['title']} {data['meta']}"
        cashback = extract_cashback_rate(combined)
        bon_achat = extract_bon_achat_rate(combined)
        
        if cashback or bon_achat:
            return {'url': url, 'cashback': cashback, 'bon_achat': bon_achat}
        return None
    
    def scrape_ebuyclub(self, slug, merchant_id):
        """Scrape eBuyClub"""
        if not merchant_id or not slug:
            return None
        
        url = f"https://www.ebuyclub.com/reduction-{slug}-{merchant_id}"
        data = self.get_page_meta(url)
        if not data:
            return None
        
        # eBuyClub : le cashback est dans le titre format "X% Cashback"
        combined = f"{data['title']} {data['meta']}"
        cashback = extract_cashback_rate(combined)
        bon_achat = extract_bon_achat_rate(combined)
        
        if cashback or bon_achat:
            return {'url': url, 'cashback': cashback, 'bon_achat': bon_achat}
        return None
    
    def scrape_merchant(self, merchant_data):
        """Scrape toutes les plateformes pour un marchand"""
        name, slug_p, slug_w, id_eb, category, emoji = merchant_data
        
        print(f"{emoji} {name}...", end=" ", flush=True)
        
        offers = []
        
        # Poulpeo
        if slug_p:
            result = self.scrape_poulpeo(slug_p)
            if result:
                if result['cashback']:
                    offers.append({
                        "platform": "Poulpeo",
                        "type": "cashback",
                        "rate": result['cashback'],
                        "url": result['url']
                    })
                if result['bon_achat']:
                    offers.append({
                        "platform": "Poulpeo",
                        "type": "bon_achat",
                        "rate": result['bon_achat'],
                        "url": result['url']
                    })
            time.sleep(0.3)
        
        # Widilo
        if slug_w:
            result = self.scrape_widilo(slug_w)
            if result:
                if result['cashback']:
                    offers.append({
                        "platform": "Widilo",
                        "type": "cashback",
                        "rate": result['cashback'],
                        "url": result['url']
                    })
                if result['bon_achat']:
                    offers.append({
                        "platform": "Widilo",
                        "type": "bon_achat",
                        "rate": result['bon_achat'],
                        "url": result['url']
                    })
            time.sleep(0.3)
        
        # eBuyClub
        if id_eb and slug_p:
            result = self.scrape_ebuyclub(slug_p, id_eb)
            if result:
                if result['cashback']:
                    offers.append({
                        "platform": "eBuyClub",
                        "type": "cashback",
                        "rate": result['cashback'],
                        "url": result['url']
                    })
                if result['bon_achat']:
                    offers.append({
                        "platform": "eBuyClub",
                        "type": "bon_achat",
                        "rate": result['bon_achat'],
                        "url": result['url']
                    })
            time.sleep(0.3)
        
        # Calcul des meilleurs taux
        cashback_offers = [o for o in offers if o['type'] == 'cashback']
        bon_achat_offers = [o for o in offers if o['type'] == 'bon_achat']
        
        best_cashback = max(cashback_offers, key=lambda x: x['rate']) if cashback_offers else None
        best_bon_achat = max(bon_achat_offers, key=lambda x: x['rate']) if bon_achat_offers else None
        
        # Log
        parts = []
        if best_cashback:
            parts.append(f"CB:{best_cashback['rate']}%/{best_cashback['platform']}")
        if best_bon_achat:
            parts.append(f"BA:{best_bon_achat['rate']}%/{best_bon_achat['platform']}")
        
        if parts:
            print(f"✅ {' | '.join(parts)}")
        else:
            print("❌ Aucune offre")
        
        if offers:
            return {
                "name": name,
                "slug": slug_p or slug_w,
                "category": category,
                "logo": emoji,
                "offers": offers,
                "best_cashback": {
                    "rate": best_cashback['rate'],
                    "platform": best_cashback['platform'],
                    "url": best_cashback['url']
                } if best_cashback else None,
                "best_bon_achat": {
                    "rate": best_bon_achat['rate'],
                    "platform": best_bon_achat['platform'],
                    "url": best_bon_achat['url']
                } if best_bon_achat else None,
                "best_rate": best_cashback['rate'] if best_cashback else (best_bon_achat['rate'] if best_bon_achat else 0),
                "best_platform": best_cashback['platform'] if best_cashback else (best_bon_achat['platform'] if best_bon_achat else "")
            }
        return None
    
    def run(self):
        """Lance le scraping complet"""
        print("=" * 70)
        print("CASHBACKITO SCRAPER V5")
        print("=" * 70)
        print(f"Date: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        print(f"Marchands: {len(MERCHANTS)}")
        print(f"Plateformes: Poulpeo, Widilo, eBuyClub")
        print("-" * 70)
        
        merchants_data = []
        no_offers = []
        
        for merchant in MERCHANTS:
            result = self.scrape_merchant(merchant)
            if result:
                merchants_data.append(result)
            else:
                no_offers.append(merchant[0])
        
        # Stats
        total_offers = sum(len(m.get('offers', [])) for m in merchants_data)
        merchants_with_cashback = sum(1 for m in merchants_data if m.get('best_cashback'))
        merchants_with_bon_achat = sum(1 for m in merchants_data if m.get('best_bon_achat'))
        
        output = {
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "last_updated_fr": datetime.now().strftime('%d/%m/%Y à %Hh%M'),
            "version": "5.0",
            "stats": {
                "merchants_total": len(MERCHANTS),
                "merchants_with_offers": len(merchants_data),
                "merchants_with_cashback": merchants_with_cashback,
                "merchants_with_bon_achat": merchants_with_bon_achat,
                "total_offers": total_offers,
                "platforms": ["Poulpeo", "Widilo", "eBuyClub"]
            },
            "merchants": merchants_data
        }
        
        # Sauvegarder
        output_dir = Path(__file__).parent / "data"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "cashback_rates.json"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        
        print("-" * 70)
        print("RÉSULTATS")
        print("-" * 70)
        print(f"📊 Marchands avec offres: {len(merchants_data)}/{len(MERCHANTS)}")
        print(f"💰 Avec cashback: {merchants_with_cashback}")
        print(f"🎁 Avec bons d'achat: {merchants_with_bon_achat}")
        print(f"📈 Total offres: {total_offers}")
        
        if no_offers:
            print(f"\n⚠️  Sans offre: {', '.join(no_offers)}")
        
        # Stats par plateforme
        platform_stats = {}
        for m in merchants_data:
            for o in m.get('offers', []):
                key = f"{o['platform']}_{o['type']}"
                platform_stats[key] = platform_stats.get(key, 0) + 1
        
        print(f"\n📋 Par plateforme:")
        for key, count in sorted(platform_stats.items(), key=lambda x: -x[1]):
            platform, offer_type = key.rsplit('_', 1)
            icon = "💰" if offer_type == "cashback" else "🎁"
            print(f"   {icon} {platform}: {count}")
        
        print(f"\n✅ Fichier: {output_path}")
        
        return output


if __name__ == "__main__":
    scraper = CashbackScraper()
    scraper.run()
